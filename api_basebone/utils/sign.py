import logging

import time
import hashlib

from django.conf import settings

from .uuid import uuid4_hex


logger = logging.getLogger('django')


def common_make_sign(api_key=None, secret=None, timestamp=None, noncestr=None):
    """通用产生签名"""
    string_sign_temp = 'key={}&secret={}&timestamp={}&nonce_str={}'.format(
        api_key, secret, timestamp, noncestr
    )
    return hashlib.md5(string_sign_temp.encode('utf-8')).hexdigest().upper()


def build_common_header():
    """接收业务方数据通信的请求头设置"""

    timestamp = str(int(time.time()))
    noncestr = uuid4_hex()
    key = settings.BUSINESS_KEY
    secret = settings.BUSINESS_SECRET
    sign_str = common_make_sign(key, secret, timestamp, noncestr)

    headers = {
        'Content-Type': 'application/json',
        'X_API_SIGNATURE': sign_str,
        'X_API_KEY': key,
        'X_API_TIMESTAMP': timestamp,
        'X_API_NONCESTR': noncestr,
    }
    return headers
