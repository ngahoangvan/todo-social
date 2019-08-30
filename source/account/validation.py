from django.contrib.auth.models import User
from tastypie.validation import Validation


class UserProfileValidation(Validation):
    def is_valid(self, bundle, request=None):
        print("validation successfull")
        print(bundle)
        errors = {}
        return errors
