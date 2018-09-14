import re
from django.conf.urls import url
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import validate_email
from tastypie.resources import ModelResource
from tastypie.http import HttpUnauthorized, HttpForbidden
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from tastypie import fields
from .models import Profile, Relationship
from .authorization import UserObjectsOnlyAuthorization
from .validation import UserProfileValidation

class UserResource(ModelResource):
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

    # def dehydrate(self, bundle):
    #     bundle.data['user_id'] = bundle.obj.user.id
    #     bundle.data['username'] = bundle.obj.user.username
    #     bundle.data['first_name'] = bundle.obj.user.first_name
    #     bundle.data['last_name'] = bundle.obj.user.last_name
    #     return bundle

    def hydrate_user(self, bundle):
        user = User.objects.get(id=bundle.obj.user_id)
        user.first_name = bundle.data['first_name']
        user.last_name = bundle.data['last_name']
        user.save()
        return super(ProfileResource, self).hydrate(bundle)


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
            # sign_in
            url(r"^(?P<resource_name>%s)/sign_in%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_in'), name="api_sign_in"),
            # sign_out
            url(r"^(?P<resource_name>%s)/sign_out%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_out'), name="api_sign_out"),
            # sign_up
            url(r"^(?P<resource_name>%s)/sign_up%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_up'), name="api_sign_up"),
            # recover password (InProgress)
            url(r"^(?P<resource_name>%s)/recover_password%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('recover_password'), name="api_recover_password"),
        ]

    def sign_in(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body,
                                format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')

        # Valdate username
        if bool(re.match(r'^[\w.@+-]+$', username)) is False:
            raise BadRequest('Username invalid')
        # Sign in by email
        match = re.match('^[_a-z0-9-]+(\\.[_a-z0-9-]+)*@[a-z0-9-]+(\\.[a-z0-9-]+)*(\\.[a-z]{2,4})$', username)
        if match is not None:
            if User.objects.filter(email=username).exists():
                user = User.objects.get(email=username)
                username = user.username
            else:
                raise BadRequest('You were sign in by email, but email is not exist')
                
        # Validate password
        validate_password(password)

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
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        # Data of Profile (unnecessary)
        other_name = data.get('other_name', '').strip()
        address = data.get('address', '').strip()
        birthday = data.get('birthday')
        phone_number = data.get('phone_number', '').strip()
        photo_url = data.get('photo_url', '').strip()

        # Valdate username
        if bool(re.match(r'^[\w.@+-]+$', username)) is False:
            raise BadRequest('Username invalid')
        elif User.objects.filter(username=username).exists():
            raise BadRequest('Username already exists')

        # Validate password
        validate_password(password)

        # Validate email
        validate_email(email)
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

    def recover_password(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        data = self.deserialize(request, request.body,
                                format=request.META.get('CONTENT_TYPE', 'application/join'))
        email = data['email']
        try:
            user = User.objects.get(email=email)
 
        except User.DoesNotExist:
            raise BadRequest("User with email %s not found" % email)
        # Send Code to user email (InProgress.....)
        return self.create_response(request, {'success': True})

class RelationshipResource(ModelResource):
    user_one = fields.ForeignKey(UserResource, attribute='user_one', full=True)
    user_two = fields.ForeignKey(UserResource, attribute='user_two', full=True)
    class Meta:
        queryset = Relationship.objects.all()
        resource_name = 'relationship'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        include_resource_uri = False


# class AuthenticationResource2(ModelResource):
#     class Meta:
#         queryset = User.objects.all()
#         excludes = ['password', 'is_superuser']
#         allowed_methods = ['get', 'post']
#         resource_name = 'test'
#         authentication = ApiKeyAuthentication()
#         authorization = Authorization()
#         always_return_data = True

#     def prepend_urls(self):
#         return [
#             # sign_in
#             url(r"^(?P<resource_name>%s)/sign_in%s$" %
#                 (self._meta.resource_name, trailing_slash()),
#                 self.wrap_view('sign_in'), name="api_sign_in")
#         ]

#     def sign_in(self, request, **kwargs):
#         print(request.user)
#         print(request.username)
#         return self.create_response(request, {
#             'success': False,
#             'reason': 'incorrect',
#         }, HttpUnauthorized)
