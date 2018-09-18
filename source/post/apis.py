from django.conf.urls import url
from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.exceptions import BadRequest
from tastypie import fields
from source.account.apis import UserResource
from .models import Post, Like, Comment
from .authorization import UserPostObjectsOnlyAuthorization

class PostResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)

    class Meta:
        queryset = Post.objects.all()
        resource_name = 'posts'
        allowed_methods = ['get']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserPostObjectsOnlyAuthorization()
        always_return_data = True
        ordering = ['id']

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<name>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]


class LikeResource(ModelResource):

    class Meta:
        queryset = Like.objects.all()
        resource_name = 'likes'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True


class CommentResource(ModelResource):
    class Meta:
        queryset = Comment.objects.all()
        resource_name = 'comments'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
