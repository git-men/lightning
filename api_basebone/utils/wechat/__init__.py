from django.conf import settings
from wechatpy.client import WeChatClient
from wechatpy.client.api import WeChatWxa
from wechatpy.pay.api import WeChatRefund
from wechatpy.session.redisstorage import RedisStorage
from api_basebone.utils.redis import redis_client

session = RedisStorage(redis_client)


def wrap(api, app_id, app_secret=None):
    return api(
        client=WeChatClient(appid=app_id, secret=app_secret or settings.WECHAT_APP_MAP[app_id]['appsecret'], session=session)
    )


def wxa(app_id, app_secret=None):
    return wrap(WeChatWxa, app_id=app_id, app_secret=app_secret)


def refund(app_id, app_secret=None):
    return wrap(WeChatRefund, app_id=app_id, app_secret=app_secret)
