from django.conf.urls import url

# from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication, Authentication

# from tastypie.exceptions import BadRequest
from tastypie import fields
from ..account.apis import UserResource
from ..account.models import Relationship
from ..commons.custom_exception import CustomBadRequest
from .models import Post, Like, Comment
from .authorization import (
    UserPostObjectsOnlyAuthorization,
    UserCommentObjectsOnlyAuthorization,
)


class LikeResource(ModelResource):
    author = fields.ForeignKey(UserResource, "author")
    # post = fields.ForeignKey(PostResource, 'post')

    class Meta:
        queryset = Like.objects.all()
        resource_name = "likes"
        allowed_methods = ["get", "post"]
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/liked/$"
                % (self._meta.resource_name),
                self.wrap_view("like_post"),
                name="api_like_post",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/disliked/$"
                % (self._meta.resource_name),
                self.wrap_view("disliked_post"),
                name="api_disliked_post",
            ),
        ]


class CommentResource(ModelResource):
    author = fields.ForeignKey(UserResource, "author", full=True)
    post = fields.ForeignKey(
        "source.post.apis.PostResource", "post", full=True
    )

    class Meta:
        queryset = Comment.objects.all()
        resource_name = "comments"
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserCommentObjectsOnlyAuthorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"(?P<pk>[\w\d_.-]+)/commented/$",
                self.wrap_view("dispatch_list"),
                name="api_dispatch_list",
            )
        ]

    def obj_create(self, bundle, **kwargs):
        post_id = bundle.request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        post.comments_count += 1
        post.save()
        return super(CommentResource, self).obj_create(
            bundle, post_id=post_id, author=bundle.request.user
        )


class PostResource(ModelResource):
    author = fields.ForeignKey(UserResource, "author", full=True)
    list_comment = fields.ToManyField(
        CommentResource, "post_commented", null=True
    )

    class Meta:
        queryset = Post.objects.all()
        resource_name = "posts"
        allowed_methods = ["get", "post", "put", "patch", "delete"]
        include_resource_uri = False
        authentication = Authentication()
        authorization = UserPostObjectsOnlyAuthorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/other/(?P<name>[\w\d_.-]+)/$"
                % (self._meta.resource_name),
                self.wrap_view("other_post"),
                name="api_orther_post",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/liked/$"
                % (self._meta.resource_name),
                self.wrap_view("like_post"),
                name="api_like_post",
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/disliked/$"
                % (self._meta.resource_name),
                self.wrap_view("disliked_post"),
                name="api_disliked_post",
            ),
        ]

    def like_post(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_id = request.user.id
        if user_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        post_id = request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        if Like.objects.filter(author=user_id, post_id=post_id).exists():
            raise CustomBadRequest(error_message="You liked this post")
        if post is not None:
            Like.objects.create(author_id=user_id, post_id=post_id)
            post.like_count += 1
            post.save()

        return self.create_response(request, {"success": True})

    def disliked_post(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_id = request.user.id
        if user_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        post_id = request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        if post is not None:
            if Like.objects.filter(author=user_id, post_id=post_id).exists():
                liked = Like.objects.get(author=user_id, post_id=post_id)
                liked.delete()
            post.like_count -= 1
            post.save()
        else:
            raise CustomBadRequest(error_message="Can not find this post")

        return self.create_response(request, {"success": True})

    # def other_post(self, request, **kwargs):
    #     self.method_check(request, allowed=['get'])
    #     try:
    #         name = request.resolver_match.kwargs["name"]
    #         user = User.objects.get(username=name)
    #     except KeyError:
    #         return BadRequest('Cannot find this user')
    #     return PostResource().get_list(request, author=user)

    def obj_create(self, bundle, **kwargs):
        return super(PostResource, self).obj_create(
            bundle, author=bundle.request.user
        )
