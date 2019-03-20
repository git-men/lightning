from rest_framework.permissions import IsAdminUser as OriginIsAdminUser
from django.conf import settings


from api_basebone.utils.sign import common_make_sign


class IsAdminUser(OriginIsAdminUser):
    """
    Allows access only to admin users.

    这里使用了签名认证和原有的会话认证

    如果请求的头部包含了签名的参数，则使用签名校验，否则使用
    原有的会话认证
    """

    def check_with_sign(self, request):
        meta = request.META
        sign_key_list = [
            'HTTP_X_API_TIMESTAMP',
            'HTTP_X_API_NONCESTR',
            'HTTP_X_API_SIGNATURE',
        ]
        return all([key in meta for key in sign_key_list])

    def validate_sign(self, request):
        """校验签名是否正常"""
        key = settings.BUSINESS_KEY
        secret = settings.BUSINESS_SECRET
        timestamp = request.META.get('HTTP_X_API_TIMESTAMP')
        noncestr = request.META.get('HTTP_X_API_NONCESTR')
        sign = request.META.get('HTTP_X_API_SIGNATURE')
        return sign == common_make_sign(key, secret, timestamp, noncestr)

    def has_permission(self, request, view):
        if not self.check_with_sign(request):
            return request.user and request.user.is_staff
        else:
            return self.validate_sign(request)
