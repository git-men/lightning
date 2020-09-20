from django.conf import settings
from django.core.cache import cache
from wechatpy.client import WeChatClient
from wechatpy.client.api import WeChatWxa
from wechatpy.session.redisstorage import RedisStorage
from wechatpy.session.memorystorage import MemoryStorage

from django_redis import get_redis_connection

session = RedisStorage(get_redis_connection())\
    if settings.CACHES['default']['BACKEND'] == 'django_redis.cache.RedisCache'\
        else MemoryStorage()


def wrap(api, app_id, app_secret=None):
    return api(client=WeChatClient(
        appid=app_id,
        secret=app_secret or settings.WECHAT_APP_MAP[app_id]['appsecret'],
        session=session))


def wxa(app_id, app_secret=None):
    return wrap(WeChatWxa, app_id=app_id, app_secret=app_secret)


def wechat_client(app_id, app_secret=None):
    return WeChatClient(app_id,
                        secret=app_secret
                        or settings.WECHAT_APP_MAP[app_id]['appsecret'],
                        session=session)
