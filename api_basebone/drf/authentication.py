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
            try:
                body_str = json.dumps(request.data, ensure_ascii=False, separators=(',', ':'))
            except:
                pass  # multipart/form-data请求不能序列化，先跳过
            else:
                sign = hashlib.sha256(body_str.encode()).hexdigest()
                if sign != request.META['HTTP_X_SIGNATURE']:
                    raise PermissionDenied()
        return super().authenticate(request)
