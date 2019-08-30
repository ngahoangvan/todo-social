from __future__ import absolute_import
import json
from tastypie.exceptions import TastypieError
from tastypie.http import HttpBadRequest
from .constants import ERRORS_CODE


class CustomBadRequest(TastypieError):
    class META:
        abstract = True

    def __init__(
        self, error_type=None, field="", error_message=None, obj="Object"
    ):
        error = ERRORS_CODE.get(error_type)
        if error:
            code = error["code"]
            message = error["message"].format(field=field, obj=obj)
        else:
            code = 400
            message = "Nothing"

        if error_message is not None:
            message = error_message

        self._response = {"error": {"code": code, "message": message}}

    @property
    def response(self):
        return HttpBadRequest(
            json.dumps(self._response), content_type="application/json"
        )
