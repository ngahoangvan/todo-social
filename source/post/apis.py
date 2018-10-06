from django.conf.urls import url
from django.contrib.auth.models import User
from tastypie.resources import ModelResource, ALL
from tastypie.authorization import Authorization
from tastypie.authentication import  ApiKeyAuthentication
from tastypie.exceptions import BadRequest
from tastypie import fields
from  ..account.apis import UserResource
from .models import Post, Like, Comment
from .authorization import (
    UserPostObjectsOnlyAuthorization,
    UserCommentObjectsOnlyAuthorization
)

class PostResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)

    class Meta:
        queryset = Post.objects.all()
        resource_name = 'posts'
        allowed_methods = ['get', 'post', 'put', 'patch', 'delete']
        filtering = {
            'slug': ALL,
            'author': ALL,
        }
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserPostObjectsOnlyAuthorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/other/(?P<name>[\w\d_.-]+)/$" %
                (self._meta.resource_name),
                self.wrap_view('other_post'), name="api_orther_post"),
        ]

    def other_post(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        try:
            name = request.resolver_match.kwargs["name"]
            user = User.objects.get(username=name)
        except KeyError:
            return BadRequest('Cannot find this user')
        post_resource = PostResource()
        return post_resource.get_list(request, author=user)

    def obj_create(self, bundle, **kwargs):
        return super(PostResource, self).obj_create(bundle, author=bundle.request.user)

    # def dehydrate(self, bundle):
    #     # print(super(PostResource, self))
    #     # print(bundle.data['author']['profile'])
    #     return super(PostResource, self).dehydrate(bundle)

class LikeResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)
    post = fields.ForeignKey(PostResource, 'post', full=True)

    class Meta:
        queryset = Like.objects.all()
        resource_name = 'likes'
        allowed_methods = ['get', 'post']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/liked/$" %
                (self._meta.resource_name),
                self.wrap_view('like_post'), name="api_like_post"),
            url(r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/disliked/$" %
                (self._meta.resource_name),
                self.wrap_view('disliked_post'), name="api_disliked_post"),
        ]

    def like_post(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        user_id = request.user.id
        if user_id is None:
            raise BadRequest('Please signin first')
        post_id = request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        if Like.objects.filter(author=user_id, post_id=post_id).exists():
            raise BadRequest('You liked this post')
        if post is not None:
            Like.objects.create(author_id=user_id, post_id=post_id)
            post.like_count += 1
            post.save()

        return self.create_response(request, {
            'success': True
        })

    def disliked_post(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        user_id = request.user.id
        if user_id is None:
            raise BadRequest('Please signin first')
        post_id = request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        if post is not None:
            if Like.objects.filter(author=user_id, post_id=post_id).exists():
                liked = Like.objects.get(author=user_id, post_id=post_id)
                liked.delete()
            post.like_count -= 1
            post.save()
        else:
            raise BadRequest('Can not find this post')

        return self.create_response(request, {
            'success': True
        })

    # def dehydrate(self, bundle):
    #     # if "profile" in bundle.data['author']:
    #     #     bundle.data.pop('profile')
    #     print(bundle.data['author'])
    #     return super(LikeResource, self).dehydrate(bundle)


class CommentResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)
    post = fields.ForeignKey(PostResource, 'post', full=True)
    class Meta:
        queryset = Comment.objects.all()
        resource_name = 'comments'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserCommentObjectsOnlyAuthorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/commented/$" % self._meta.resource_name,
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^post/(?P<pk>[\w\d_.-]+)/(?P<resource_name>%s)/all/$" %
                (self._meta.resource_name),
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

    # def show_comment(self, request, **kwargs):
    #     self.method_check(request, allowed=['get'])
    #     post_id = request.resolver_match.kwargs["pk"]
    #     list_comment = Comment.objects.filter(post_id=post_id)
    #     print(list_comment)
    #     print(dir(self.get_object_list(request).filter(post_id=post_id).values()))
    #     print(self.get_object_list(request).filter(post_id=post_id).values())
    #     for i in self.get_object_list(request).filter(post_id=post_id).values():
    #         print(i)
    #     return self.create_response(request, {
    #         self.get_object_list(request).filter(post_id=post_id).values()
    #     })

    def obj_create(self, bundle, **kwargs):
        post_id = bundle.request.resolver_match.kwargs["pk"]
        post = Post.objects.get(id=post_id)
        post.comments_count += 1
        post.save()
        return super(CommentResource, self) \
                .obj_create(bundle, post_id=post_id, author=bundle.request.user)

    def get_object_list(self, request):
        post_id = request.resolver_match.kwargs["pk"]
        return super(CommentResource, self).get_object_list(request).filter(post_id=post_id)

    # def hydrate_author(self, bundle):
    #     post_id = bundle.request.resolver_match.kwargs["pk"]
    #     comment = Comment.objects.get(id=post_id)
    #     print(comment)
    #     return super(CommentResource, self).hydrate(bundle)


    # def dispatch_list(self, request, **kwargs):
    #     print(request.user)
    #     post_id = request.resolver_match.kwargs["pk"]
    #     print(post_id)
    #     return self.get_list(request, **kwargs)
