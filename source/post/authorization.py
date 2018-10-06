from __future__ import absolute_import
# from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized, BadRequest
# from ...account.models import Relationship


class UserPostObjectsOnlyAuthorization(Authorization):
    def update_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no update by bundle.")

    def update_detail(self, object_list, bundle):
        return bundle.obj.author == bundle.request.user

    def delete_detail(self, object_list, bundle):
        return bundle.obj.author == bundle.request.user

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes by bundle")

class UserCommentObjectsOnlyAuthorization(Authorization):
    pass
    # def read_list(self, object_list, bundle):
    #     print(bundle.request.user)
    #     post_id = bundle.request.resolver_match.kwargs["pk"]
    #     print(post_id)
    #     return super().read_list(object_list, bundle).filter(post_id=post_id)

    # def create_list(self, object_list, bundle):
    #     post_id = bundle.request.resolver_match.kwargs["pk"]
    #     print(post_id)
    #     print(object_list)
    #     # return super().create_list(object_list, bundle)

    # def create_detail(self, object_list, bundle):
    #     post_id = bundle.request.resolver_match.kwargs["pk"]
    #     print(post_id)
    #     # return super().create_detail(object_list, bundle)
