import arrow
import base64
import datetime
import hmac
import json
import logging
import oss2

from hashlib import sha1
from django.conf import settings

from bsm_config.settings import site_setting

logger = logging.getLogger('django')


class AliYunOSS:
    """阿里云 OSS 类"""

    OSS_ENDPOINT = 'ALI_YUN_OSS_ENDPOINT'
    OSS_KEY = 'ALI_YUN_OSS_KEY'
    OSS_SECRET = 'ALI_YUN_OSS_SECRET'
    OSS_HOST = 'ALI_YUN_OSS_HOST'
    OSS_BUCKET = 'ALI_YUN_OSS_BUCKET'
    OSS_CDN_HOST = 'ALI_YUN_OSS_CDN_HOST'
    UPLOAD_DIR = 'UPLOAD_DIR'

    
    def __init__(self, *args, **kwargs):
        self._auth = None
        self._service = None
        self._bucket = None

    @property
    def auth(self):
        if self._auth is None:
            self._auth = oss2.Auth(site_setting[self.OSS_KEY], site_setting[self.OSS_SECRET])
        return self._auth

    @property
    def service(self):
        if self._service is None:
            self._service = oss2.Service(self.auth, site_setting[self.OSS_ENDPOINT])
        return self._service

    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = oss2.Bucket(self.auth, site_setting[self.OSS_ENDPOINT], site_setting[self.OSS_BUCKET])
        return self._bucket

    def local_timestamp(self):
        return arrow.utcnow().to(settings.TIME_ZONE).timestamp

    def get_iso_8601(self, expire):
        return datetime.datetime.fromtimestamp(expire).isoformat() + 'Z'

    def get_token(self):
        expire_time, upload_dir = 900,  site_setting[self.UPLOAD_DIR] or 'media/'
        expire_syncpoint = self.local_timestamp() + expire_time
        expire = self.get_iso_8601(expire_syncpoint)
        policy_dict = {
            'expiration': expire,
            'conditions': [
                ['starts-with', '$key', upload_dir]
            ]
        }

        policy_encode = base64.b64encode(json.dumps(policy_dict).strip().encode())
        h = hmac.new(site_setting[self.OSS_SECRET].encode(), policy_encode, sha1)
        sign_result = base64.encodebytes(h.digest()).strip()

        token_dict = {
            'accessid': site_setting[self.OSS_KEY],
            'host': site_setting[self.OSS_HOST],
            'cdn_host': site_setting[self.OSS_CDN_HOST],
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
                return f'{site_setting[self.OSS_CDN_HOST]}/{remote_file}'

            logger.error(f'upload to aliyun oss faile {status}')
        except Exception as e:
            logger.error(f'upload to aliyun oss faile {e}')
    
    def upload_object(self, key, data, replace=True):
        """上传内容
        """
        # try:
        if not replace and self.bucket.object_exists(key):
            return f'{site_setting[self.OSS_CDN_HOST]}/{key}'
        status = self.bucket.put_object(key, data).status
        if status == 200:
            return f'{site_setting[self.OSS_CDN_HOST]}/{key}'
        # except Exception:
        #     print('what the hell?')
        #     logger.error(f'upload object {key} fail ', exc_info=True)
        

aliyun = AliYunOSS()
