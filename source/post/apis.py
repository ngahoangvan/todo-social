from django.conf.urls import url
from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.exceptions import BadRequest
from tastypie import fields
from .models import Post
from source.account.apis import UserResource

class PostResource(ModelResource):
    author = fields.ForeignKey(UserResource, 'author', full=True)

    class Meta:
        queryset = Post.objects.all()
        resource_name = 'posts'
        allowed_methods = ['get']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        order_by = ['id']

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<name>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

    def dispatch_list(self, request, **kwargs):
        name = request.resolver_match.kwargs["name"]
        user = User.objects.get(username=name)
        # print(self.get_list(request, **kwargs))
        print(request)
        return self.get_list(request, **kwargs)

    # def authorized_read_list(self, object_list, bundle):
    #     name = bundle.request.resolver_match.kwargs["name"]
    #     user = User.objects.get(username=name)
    #     return object_list.filter(author=user).select_related()
