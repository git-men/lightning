import json
import hashlib

from rest_framework.exceptions import PermissionDenied
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        pass


class SignatureSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        if request.data:
            body_str = json.dumps(request.data, ensure_ascii=False, separators=(',', ':'))
            sign = hashlib.sha256(body_str.encode()).hexdigest()
            if sign != request.META['HTTP_X_SIGNATURE']:
                return PermissionDenied()
        return super().authenticate(request)
