from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.restful.serializers import create_serializer_class
from api_basebone.utils import tencent
from api_basebone.utils.aliyun import aliyun
from bsm_config.settings import site_setting


class UploadViewSet(viewsets.GenericViewSet):
    """通用上传接口"""

    permission_classes = (permissions.IsAuthenticated,)

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

        #### 腾讯云 COS 返回的数据结构如下
        {
            'startTime': 1592561936
            'expiredTime': 1592561966,
            'expiration': '2020-06-19T10:19:26Z',
            'requestId': '4332ced3-50a7-48fb-a35a-cb9efcec95d9',
            'bucket': 'test-20188932',
            'region': 'ap-guangzhou',
            'credentials': {
                'sessionToken': 'kg1Mg_UmDtAJ3wQA',
                'tmpSecretId': 'AKIDy_RmF9qEg1geYsrJ_UwR4WWYcDGM2iy71R',
                'tmpSecretKey': 'Q5FPMVsD='
            },
        }
        """
        service = request.query_params.get('service', site_setting['upload_provider'])
        result = {'provider': None}
        if service in ['aliyun', 'oss']:
            result = aliyun.get_token()
            result['provider'] = 'oss'
        elif service in ['tencent', 'cos']:
            result = tencent.post_object_token()
            result['provider'] = 'cos'
        elif service == 'file_storage':
            result = {'provider': 'file_storage', 'policy': '', 'dir': '', 'host': '/basebone/storage/upload'}
        return success_response(result)
