from django.conf import settings

from sts.sts import Sts

"""
腾讯参考文档 https://github.com/tencentyun/qcloud-cos-sts-sdk/tree/master/python

在 settings.py 中进行配置
env = environ.Env(
    ...
    QCLOUD_APPID=(int, 1255222202),
    QCLOUD_SECRET_ID=(str, 'AKIDCG8pJeQsukS1OYHJvX2PfjhZHo9IRLFC'),
    QCLOUD_SECRET_KEY=(str, 'vffU7YosmYefV9f5MRQIyUsBNrDPPCoD'),
    QCLOUD_COS_BUCKET=(str, 'test-1255222202'),
    QCLOUD_COS_DURATION_SECONDS = (int, 300),
    QCLOUD_COS_REGION=(str, 'ap-guangzhou'),
    ...
)

# 腾讯云 COS 配置
QCLOUD_APPID = env.int('QCLOUD_APPID')
QCLOUD_SECRET_ID = env('QCLOUD_SECRET_ID')
QCLOUD_SECRET_KEY = env('QCLOUD_SECRET_KEY')
QCLOUD_COS_BUCKET = env('QCLOUD_COS_BUCKET')
QCLOUD_COS_DURATION_SECONDS = env('QCLOUD_COS_DURATION_SECONDS')
QCLOUD_COS_REGION = env('QCLOUD_COS_REGION')
"""


def get_credential():
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': settings.QCLOUD_COS_DURATION_SECONDS,
        # 固定密钥 id
        'secret_id': settings.QCLOUD_SECRET_ID,
        # 固定密钥 key
        'secret_key': settings.QCLOUD_SECRET_KEY,
        # 换成你的 bucket
        'bucket': settings.QCLOUD_COS_BUCKET,
        # 换成 bucket 所在地区
        'region': settings.QCLOUD_COS_REGION,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的目录，例子：* 或者 a/* 或者 a.jpg
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            'name/cos:PostObject',
            # 分片上传
            'name/cos:InitiateMultipartUpload',
            'name/cos:ListMultipartUploads',
            'name/cos:ListParts',
            'name/cos:UploadPart',
            'name/cos:CompleteMultipartUpload',
        ],
    }

    sts = Sts(config)
    token_config = sts.get_credential()
    return token_config
