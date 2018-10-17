from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.serializers import create_serializer_class

from api_basebone.utils.aliyun import aliyun


class UploadViewSet(viewsets.GenericViewSet):
    """通用上传接口"""

    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        model = get_user_model()
        return create_serializer_class(model)

    @action(detail=False, url_path='token')
    def token(self, request, *args, **kwargs):
        """生成对应的上传签名"""
        service = request.query_params.get('service', 'aliyun')
        if service == 'aliyun':
            result = aliyun.get_token()
        else:
            result = {}
        return success_response(result)
