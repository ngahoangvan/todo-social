import re
from django.conf.urls import url
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from tastypie.resources import ModelResource, ALL
from tastypie.http import HttpUnauthorized, HttpForbidden
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication, ApiKeyAuthentication

# from tastypie.exceptions import BadRequest
from tastypie.utils import trailing_slash
from tastypie import fields
from ..commons.custom_exception import CustomBadRequest
from .models import Profile, Relationship
from .authorization import UserObjectsOnlyAuthorization
from .validation import UserProfileValidation


class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        resource_name = "user-profile"
        fields = [
            "id",
            "other_name",
            "birthday",
            "address",
            "phone_number",
            "photo_url",
        ]
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class UserResource(ModelResource):
    profile = fields.ForeignKey(
        ProfileResource, attribute="profile", full=True
    )

    class Meta:
        queryset = User.objects.all()
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile",
        ]
        resource_name = "auth/users"
        allowed_methods = ["get", "post", "put", "patch", "delete"]
        filtering = {"slug": ALL, "username": ALL}
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = UserObjectsOnlyAuthorization()

    def hydrate_profile(self, bundle):
        profile = Profile.objects.get(user_id=bundle.obj.id)
        profile.other_name = bundle.data["other_name"]
        profile.birthday = bundle.data["birthday"]
        profile.address = bundle.data["address"]
        profile.phone_number = bundle.data["phone_number"]
        profile.photo_url = bundle.data["photo_url"]
        profile.save()
        return super(UserResource, self).hydrate(bundle)


class AuthenticationResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        excludes = ["password", "is_superuser"]
        allowed_methods = ["get", "post"]
        resource_name = "authentication"
        authentication = Authentication()
        authorization = Authorization()
        always_return_data = True
        validation = UserProfileValidation()

    def prepend_urls(self):
        return [
            # sign_in
            url(
                r"^(?P<resource_name>%s)/sign_in%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("sign_in"),
                name="api_sign_in",
            ),
            # sign_out
            url(
                r"^(?P<resource_name>%s)/sign_out%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("sign_out"),
                name="api_sign_out",
            ),
            # sign_up
            url(
                r"^(?P<resource_name>%s)/sign_up%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("sign_up"),
                name="api_sign_up",
            ),
            # recover password (InProgress)
            url(
                r"^(?P<resource_name>%s)/recover_password%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("recover_password"),
                name="api_recover_password",
            ),
        ]

    def sign_in(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        data = self.deserialize(
            request,
            request.body,
            format=request.META.get("CONTENT_TYPE", "application/json"),
        )

        username = data.get("username", "")
        password = data.get("password", "")

        # Valdate username
        if bool(re.match(r"^[\w.@+-]+$", username)) is False:
            raise CustomBadRequest(error_message="Username invalid")
        # Sign in by email
        match = re.match(
            "^[_a-z0-9-]+(\\.[_a-z0-9-]+)*@[a-z0-9-]+(\\.[a-z0-9-]+)*(\\.[a-z]{2,4})$",
            username,
        )
        if match is not None:
            if User.objects.filter(email=username).exists():
                user = User.objects.get(email=username)
                username = user.username
            else:
                raise CustomBadRequest(
                    error_type="UNAUTHORIZED",
                    error_message="You were sign in by email, but email is not exist",
                )
        # Validate password
        validate_password(password)

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return self.create_response(
                    request,
                    {
                        "success": True,
                        "id": user.id,
                        "username": user.username,
                        "api_key": user.api_key.key,
                    },
                )
            else:
                return self.create_response(
                    request,
                    {"success": False, "reason": "disabled"},
                    HttpForbidden,
                )
        else:
            return self.create_response(
                request,
                {"success": False, "reason": "incorrect"},
                HttpUnauthorized,
            )

    def sign_out(self, request, **kwargs):
        self.is_authenticated(request)
        self.method_check(request, allowed=["get"])
        if request.user and request.user.is_authenticated:
            logout(request)
            return self.create_response(request, {"success": True})
        else:
            return self.create_response(
                request,
                {
                    "success": False,
                    "error_message": "You are \
                                                  not authenticated, %s"
                    % request.user.is_authenticated,
                },
            )

    def sign_up(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        data = self.deserialize(
            request,
            request.body,
            format=request.META.get("CONTENT_TYPE", "application/join"),
        )
        # Data of Account
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        email = data.get("email", "").strip()
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        # Data of Profile (unnecessary)
        other_name = data.get("other_name", "").strip()
        address = data.get("address", "").strip()
        birthday = data.get("birthday")
        phone_number = data.get("phone_number", "").strip()
        photo_url = data.get("photo_url", "").strip()

        # Valdate username
        if bool(re.match(r"^[\w.@+-]+$", username)) is False:
            raise CustomBadRequest(error_message="Username invalid")
        elif User.objects.filter(username=username).exists():
            raise CustomBadRequest(
                error_type="DUPLICATE_VALUE",
                error_message="Username already exists",
            )

        # Validate password
        validate_password(password)

        # Validate email
        validate_email(email)
        if User.objects.filter(email=email).exists():
            raise CustomBadRequest(
                error_type="DUPLICATE_VALUE",
                error_message="This email already \
                                   has been registered by another account",
            )
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            user = authenticate(username=username, password=password)
            login(request, user)
            if user is not None:
                Profile.objects.create(
                    user_id=user.id,
                    other_name=other_name,
                    address=address,
                    birthday=birthday,
                    phone_number=phone_number,
                    photo_url=photo_url,
                )
            else:
                raise CustomBadRequest(
                    error_message="Can't create userprofile"
                )

        return self.create_response(
            request,
            {
                "success": True,
                "id": user.id,
                "username": user.username,
                "api_key": user.api_key.key,
            },
        )

    def recover_password(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        data = self.deserialize(
            request,
            request.body,
            format=request.META.get("CONTENT_TYPE", "application/join"),
        )
        email = data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise CustomBadRequest(
                error_type="DOES_NOT_EXITS",
                error_message="User with email %s not found" % email,
            )
        # Send Code to user email (InProgress.....)
        return self.create_response(request, {"success": True})


class RelationshipResource(ModelResource):
    user_one = fields.ForeignKey(UserResource, attribute="user_one", full=True)
    user_two = fields.ForeignKey(UserResource, attribute="user_two", full=True)

    class Meta:
        queryset = Relationship.objects.all()
        resource_name = "relationship"
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        include_resource_uri = False

    def prepend_urls(self):
        return [
            # Sending Request
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/send_friends/$"
                % (self._meta.resource_name),
                self.wrap_view("send_request"),
                name="api_send_request",
            ),
            # Accept Request
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/accept_friends/$"
                % (self._meta.resource_name),
                self.wrap_view("accept_request"),
                name="api_accept_request",
            ),
            # Unfriend Request
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/un_friends/$"
                % (self._meta.resource_name),
                self.wrap_view("unfriends_request"),
                name="api_unfriends_request",
            ),
            # Block Request
            url(
                r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/block_friends/$"
                % (self._meta.resource_name),
                self.wrap_view("block_request"),
                name="api_block_request",
            ),
        ]

    def send_request(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_one_id = request.user.id
        if user_one_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        # user_two_id = request.GET["pk"]
        user_two_id = request.resolver_match.kwargs["pk"]
        # Check current relationship
        rela = Relationship.objects.filter(user_one_id=user_one_id).filter(
            user_two_id=user_two_id
        )
        reverse_rela = Relationship.objects.filter(
            user_one_id=user_two_id
        ).filter(user_two_id=user_one_id)
        if rela.filter(status=0).exists():
            raise CustomBadRequest(
                error_type="DOES_NOT_EXITS",
                error_message="You were send request to this user",
            )
        if rela.filter(status=2).exists():
            new_rela = rela.filter(status=2).get(user_one_id=user_one_id)
            new_rela.status = 0
            new_rela.save()
        elif reverse_rela.filter(status=1):
            raise CustomBadRequest(
                error_message="You and this user are friends "
            )
        elif reverse_rela.filter(status=3):
            raise CustomBadRequest(
                error_type="UNAUTHORIZED",
                error_message="You can't send request to this user",
            )
        else:
            Relationship.objects.create(
                user_one_id=user_one_id, user_two_id=user_two_id
            )
        return self.create_response(request, {"success": True})

    def accept_request(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_one_id = request.user.id
        if user_one_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        user_two_id = request.resolver_match.kwargs["pk"]
        reverse_rela = Relationship.objects.filter(
            user_one_id=user_two_id
        ).filter(user_two_id=user_one_id)
        if (
            reverse_rela.filter(status=0).exists()
            or reverse_rela.filter(status=3).exists()
        ):
            new_rela = reverse_rela.get(user_one_id=user_two_id)
            new_rela.status = 1
            new_rela.is_friends = True
            new_rela.save()
        elif reverse_rela.filter(status=1).exists():
            raise CustomBadRequest(
                error_message="You and this user is friends"
            )
        else:
            raise CustomBadRequest(
                error_message="You can not accept this request"
            )
        return self.create_response(request, {"success": True})

    def unfriends_request(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_one_id = request.user.id
        if user_one_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        user_two_id = request.resolver_match.kwargs["pk"]
        reverse_rela = Relationship.objects.filter(
            user_one_id=user_two_id
        ).filter(user_two_id=user_one_id)
        if (
            reverse_rela.filter(status=0).exists()
            or reverse_rela.filter(status=1).exists()
        ):
            new_rela = reverse_rela.get(user_one_id=user_two_id)
            new_rela.status = 2
            new_rela.is_friends = False
            new_rela.save()
        else:
            raise CustomBadRequest(
                error_message="You can not accept this request"
            )
        return self.create_response(request, {"success": True})

    def block_request(self, request, **kwargs):
        self.method_check(request, allowed=["post"])
        user_one_id = request.user.id
        if user_one_id is None:
            raise CustomBadRequest(
                error_type="UNAUTHORIZED", error_message="Please signin first"
            )
        user_two_id = request.resolver_match.kwargs["pk"]
        rela = Relationship.objects.filter(user_one_id=user_one_id).filter(
            user_two_id=user_two_id
        )
        if rela.filter(status=3).exists():
            raise CustomBadRequest(
                error_type="INVALID_DATA",
                error_message="You were block this user",
            )
        else:
            new_rela = rela.get(user_one_id=user_one_id)
            new_rela.status = 3
            new_rela.is_friends = False
            new_rela.save()
