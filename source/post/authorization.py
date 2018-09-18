from __future__ import absolute_import
from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized, BadRequest
from source.account.models import Relationship


class UserPostObjectsOnlyAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        try:
            name = bundle.request.resolver_match.kwargs["name"]
            user = User.objects.get(username=name)
        except KeyError:
            print(bundle.request.user)
            print(Relationship.objects.filter(user_one_id=bundle.request.user.id).filter(status=1))
            return object_list.select_related()
        return object_list.filter(author=user).select_related()
