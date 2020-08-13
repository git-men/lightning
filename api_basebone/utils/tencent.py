import arrow
import base64
import hashlib
import hmac
import json
import datetime
from sts.sts import Sts
from bsm_config.settings import site_setting
from api_basebone.utils.timezone import local_timestamp

"""
腾讯参考文档 https://github.com/tencentyun/qcloud-cos-sts-sdk/tree/master/python

在 site_settings.py 中 进行配置
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

setting = {
    ...
    # 腾讯 COS 配置
    'QCLOUD_APPID',
    'QCLOUD_SECRET_ID',
    'QCLOUD_SECRET_KEY',
    'QCLOUD_COS_BUCKET',
    'QCLOUD_COS_DURATION_SECONDS',
    'QCLOUD_COS_REGION',
    # 上传供应商
    'UPLOAD_PROVIDER',
    ...
}
SITE_SETTING = {e:env(e) for e in setting}
"""


def get_credential():
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': site_setting['QCLOUD_COS_DURATION_SECONDS'],
        # 固定密钥 id
        'secret_id': site_setting['QCLOUD_SECRET_ID'],
        # 固定密钥 key
        'secret_key': site_setting['QCLOUD_SECRET_KEY'],
        # 换成你的 bucket
        'bucket': site_setting['QCLOUD_COS_BUCKET'],
        # 换成 bucket 所在地区
        'region': site_setting['QCLOUD_COS_REGION'],
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
    token_config['bucket'] = config['bucket']
    token_config['region'] = config['region']
    return token_config


def post_object_token():
    now_time = datetime.datetime.now()
    expiration = (
        (now_time + datetime.timedelta(minutes=30)).replace(microsecond=0).isoformat()
    )
    expiration = f'{expiration}.000Z'

    start_timestamp = local_timestamp()
    end_timestamp = start_timestamp + 60 * 30
    key_time = f'{start_timestamp};{end_timestamp}'

    policy = {
        "expiration": expiration,
        "conditions": [
            {"bucket": site_setting['QCLOUD_COS_BUCKET']},
            {"q-sign-algorithm": "sha1"},
            {"q-ak": site_setting['QCLOUD_SECRET_ID']},
            {"q-sign-time": key_time},
        ],
    }

    # 使用 HMAC-SHA1 以 SecretKey 为密钥，以 KeyTime 为消息，计算消息摘要（哈希值），即为 SignKey。
    sign_key = hmac.new(
        site_setting['QCLOUD_SECRET_KEY'].encode('utf-8'),
        msg=key_time.encode('utf-8'),
        digestmod='sha1',
    ).hexdigest()
    # 使用 SHA1 对上文中构造的策略（Policy）文本计算消息摘要（哈希值），即为 StringToSign
    string_to_sign = hashlib.sha1(json.dumps(policy).encode('utf-8')).hexdigest()

    signature = hmac.new(
        sign_key.encode('utf-8'), msg=string_to_sign.encode('utf-8'), digestmod='sha1'
    ).hexdigest()

    bucket = site_setting['QCLOUD_COS_BUCKET']
    region = site_setting['QCLOUD_COS_REGION']

    return {
        'policy': base64.b64encode(json.dumps(policy).encode('utf-8')).decode(),
        'q_ak': site_setting['QCLOUD_SECRET_ID'],
        'key_time': key_time,
        'signature': signature,
        'host': f'https://{bucket}.cos.{region}.myqcloud.com',
        'dir': 'media/',
    }
