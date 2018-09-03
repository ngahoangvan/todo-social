from django.conf.urls import url
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from tastypie.models import ApiKey
from tastypie.resources import ModelResource
from tastypie.http import HttpUnauthorized, HttpForbidden
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from tastypie import fields
from .models import Profile

class UserResource(ModelResource):
    # profile = fields.ForeignKey(ProfileResource, 'profile', full=True)
    class Meta:
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name']
        excludes = ['email', 'password', 'is_superuser']
        resource_name = 'auth/users'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class ProfileResource(ModelResource):
    user = fields.ToOneField(UserResource, attribute='user', null=True)
    first_name = fields.CharField(attribute='user__first_name', null=True)
    last_name = fields.CharField(attribute='user__last_name', null=True)
    email = fields.CharField(attribute='user__email', null=True)
    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'user-profile'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class AuthenticationResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        excludes = ['password', 'is_superuser']
        allowed_methods = ['get', 'post']
        resource_name = 'authentication'
        authentication = Authentication()
        authorization = Authorization()
        always_return_data = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/sign_in%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_in'), name="api_sign_in"),
            url(r"^(?P<resource_name>%s)/sign_out%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_out'), name="api_sign_out"),
            url(r"^(?P<resource_name>%s)/sign_up%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_up'), name="api_sign_up"),
        ]

    def sign_in(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body,
                                format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return self.create_response(request, {
                    'success': True,
                    'api_key': user.api_key.key
                })
            else:
                return self.create_response(request, {
                    'success': False,
                    'reason': 'disabled',
                }, HttpForbidden)
        else:
            return self.create_response(request, {
                'success': False,
                'reason': 'incorrect',
            }, HttpUnauthorized)

    def sign_out(self, request, **kwargs):
        self.is_authenticated(request)
        self.method_check(request, allowed=['get'])
        if request.user and request.user.is_authenticated:
            logout(request)
            return self.create_response(request, {'success': True})
        else:
            return self.create_response(request, {'success': False,
                                                  'error_message': 'You are not authenticated, %s' % request.user.is_authenticated})

    def sign_up(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body,
                                format=request.META.get('CONTENT_TYPE', 'application/join'))
        username = data.get('username', '')
        password = data.get('password', '')
        email = data.get('email', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        # Validate in here. Update later...

        if User.objects.filter(username=username).exists():
            raise BadRequest('Username already exists')
        else:
            User.objects.create_user(username=username, email=email, password=password,
                                     first_name=first_name, last_name=last_name)
            user = authenticate(username=username, password=password)
            print(user)
            login(request, user)
            if user is not None:
                Profile.objects.create(user_id=user.id)
            else:
                raise BadRequest("Can't create userprofile")

        return self.create_response(request, {
            'success': True,
            'api_key': user.api_key.key
        })
