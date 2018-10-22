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
        """
        ## 生成对应的上传签名

        **参数放在 query string 中，形式如 ?service=aliyun**

        当前的服务只支持 (aliyun, 阿里云)

        ### Returns

        #### 阿里云的返回数据结构如下：

        ```
        {
            "error_code": "0",
            "error_message": "",
            "result": {
                "accessid": "LTAIudMj4IZMpCCn",
                "host": "speedapi.oss-cn-shanghai.aliyuncs.com",
                "policy": "eyJleHBpcmF0aW9uIjogIjIwMTgV5IiwgIm1lZGlhLyJdXX0=",
                "signature": "9aOOMFzwwVQl0u/sFgdLKRSyeIw=",
                "expire": 1539770693,
                "dir": "media/"
            }
        }
        ```
        """
        service = request.query_params.get('service', 'aliyun')
        if service == 'aliyun':
            result = aliyun.get_token()
        else:
            result = {}
        return success_response(result)
