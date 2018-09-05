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
from .authorization import UserObjectsOnlyAuthorization
from .validation import UserProfileValidation

class UserResource(ModelResource):
    # profile = fields.ForeignKey(ProfileResource, 'profile', full=True)
    class Meta:
        queryset = User.objects.all()
        fields = ['id', 'username', 'first_name', 'last_name']
        excludes = ['email', 'password', 'is_superuser']
        resource_name = 'auth/users'
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class ProfileResource(ModelResource):
    user = fields.ForeignKey(UserResource, attribute='user', full=True)

    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'user-profile'
        fields = ['id', 'other_name', 'birthday', 'address', 'phone_number',
                  'photo_url', 'user']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserObjectsOnlyAuthorization()


class AuthenticationResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        excludes = ['password', 'is_superuser']
        allowed_methods = ['get', 'post']
        resource_name = 'authentication'
        authentication = Authentication()
        authorization = Authorization()
        always_return_data = True
        validation = UserProfileValidation()

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
                    'id':user.id,
                    'username':user.username,
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
        # Data of Account
        username = data.get('username', '')
        password = data.get('password', '')
        email = data.get('email', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Data of Profile (unnecessary)
        other_name = data.get('other_name', '')
        address = data.get('address', '')
        birthday = data.get('birthday')
        phone_number = data.get('phone_number', '')
        photo_url = data.get('photo_url', '')

        # Validate in here. Update later...


        if User.objects.filter(username=username).exists():
            raise BadRequest('Username already exists')
        if User.objects.filter(email=email).exists():
            raise BadRequest('This email already has been registered by another account')
        else:
            User.objects.create_user(username=username, email=email, password=password,
                                     first_name=first_name, last_name=last_name)
            user = authenticate(username=username, password=password)
            login(request, user)
            if user is not None:
                Profile.objects.create(user_id=user.id, other_name=other_name, address=address,
                                       birthday=birthday, phone_number=phone_number, photo_url=photo_url)
            else:
                raise BadRequest("Can't create userprofile")

        return self.create_response(request, {
            'success': True,
            'id':user.id,
            'username':user.username,
            'api_key': user.api_key.key
        })
