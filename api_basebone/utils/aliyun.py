import arrow
import base64
import binascii
import datetime
import hashlib
import hmac
import json
import logging
import oss2
import requests
import random
import time

from hashlib import sha1

from django.conf import settings


class AliYunOSS:
    """阿里云 OSS 类"""

    OSS_ENDPOINT = settings.ALI_YUN_OSS_ENDPOINT
    OSS_KEY = settings.ALI_YUN_OSS_KEY
    OSS_SECRET = settings.ALI_YUN_OSS_SECRET
    OSS_HOST = settings.ALI_YUN_OSS_HOST
    OSS_BUCKET = settings.ALI_YUN_OSS_BUCKET

    def __init__(self, *args, **kwargs):
        self.auth = oss2.Auth(self.OSS_KEY, self.OSS_SECRET)
        self.service = oss2.Service(self.auth, self.OSS_ENDPOINT)
        self.bucket = oss2.Bucket(self.auth, self.OSS_ENDPOINT, self.OSS_BUCKET)

    def local_timestamp(self):
        return arrow.utcnow().to(settings.TIME_ZONE).timestamp

    def get_iso_8601(self, expire):
        return datetime.datetime.fromtimestamp(expire).isoformat() + 'Z'

    def get_token(self):
        expire_time, upload_dir = 900, 'media/'
        expire_syncpoint = self.local_timestamp() + expire_time
        expire = self.get_iso_8601(expire_syncpoint)
        policy_dict = {
            'expiration': expire,
            'conditions': [
                ['starts-with', '$key', upload_dir]
            ]
        }

        policy_encode = base64.b64encode(json.dumps(policy_dict).strip().encode())
        h = hmac.new(self.OSS_SECRET.encode(), policy_encode, sha1)
        sign_result = base64.encodestring(h.digest()).strip()

        token_dict = {
            'accessid': self.OSS_KEY,
            'host': self.OSS_HOST,
            'policy': policy_encode,
            'signature': sign_result,
            'expire': expire_syncpoint,
            'dir': upload_dir,
        }
        return token_dict

    def upload_file(self, remote_file, local_file, replace=True):
        """上传文件

        Params:
            remote_file string 远端文件名称
            local_file string 本地文件名称
            replace boolean 是否替换原文件

        Returns:
            string or None
                - string 代表上传成功
                - None 代表上传失败
        """
        status, exists = 200, False

        try:
            if not replace:
                exists = self.bucket.object_exists(remote_file)

            if not exists:
                status = self.bucket.put_object_from_file(remote_file, local_file).status

            if status == 200:
                return f'{self.OSS_HOST}/{remote_file}'

            logger.error(f'upload to aliyun oss faile {status}')
        except Exception as e:
            logger.error(f'upload to aliyun oss faile {e}')


aliyun = AliYunOSS()
