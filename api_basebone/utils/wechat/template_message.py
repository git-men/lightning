import logging
from optionaldict import optionaldict
from django.conf import settings

from wechatpy.client import WeChatClient
from wechatpy.session.redisstorage import RedisStorage
from wechatpy.session.memorystorage import MemoryStorage

from django_redis import get_redis_connection

from .form_id import FormID
from api_basebone.utils.wechat import wxa

logger = logging.getLogger('django')


def weapp_send_template_message(
    app_id,
    user_id,
    touser,
    template_id,
    data=None,
    page=None,
    color=None,
    emphasis_keyword=None,
):
    """
    发送小程序模板消息

    Params:
        app_id              是  微信应用 app_id
        user_id             是  用户主键 int
        touser	            是	接收者（用户）的 openid
        template_id	        是	所需下发的模板消息的 id
        data	            是	模板内容，不填则下发空模板
        page	            否	点击模板卡片后的跳转页面，仅限本小程序内的页面
                                支持带参数,（示例index?foo=bar）。该字段不填则模板无跳转。
        color	            否	模板内容字体的颜色，不填默认黑色 【废弃】
        emphasis_keyword	否	模板需要放大的关键词，不填则默认无放大

    Returns:
        errcode: 0,
        errmsg: "ok"
    """

    data = data if (data and isinstance(data, dict)) else {}
    formid_instance = FormID.lpop(user_id)

    if not formid_instance or not formid_instance.form_id:
        return

    try:
        form_id = formid_instance.form_id

        return wxa(app_id).send_template_message(
            touser,
            template_id,
            data,
            form_id,
            page=page,
            color=color,
            emphasis_keyword=emphasis_keyword,
        )
    except Exception as e:
        logger.error(f'weapp_send_template_error:{e}')


def weapp_send_subscribe_message(app_id, touser, template_id, data=None, page=None):
    """
    发送订阅消息

    Params:
        app_id              是  微信应用 app_id
        touser	            是	接收者（用户）的 openid
        template_id	        是	所需下发的模板消息的 id
        data	            是	模板内容，不填则下发空模板
        page	            否	点击模板卡片后的跳转页面，仅限本小程序内的页面
                                支持带参数,（示例index?foo=bar）。该字段不填则模板无跳转。

    Returns:
        errcode: 0,
        errmsg: "ok"
    """

    data = data if (data and isinstance(data, dict)) else {}

    try:
        result = wxa(app_id)._post(
            'cgi-bin/message/subscribe/send',
            data=optionaldict(
                touser=touser, template_id=template_id, page=page, data=data
            ),
        )
        return result
    except Exception as e:
        logger.error(f'weapp_send_subscribe_message:{e}')


def mp_send_template_message(
    app_id, touser, template_id, data, url=None, mini_program=None
):
    """
    发送公众号模板消息

    Params:
        app_id         是   微信应用 app_id
        touser         是   用户 ID 。 就是你收到的 `Message` 的 source
        template_id    是   模板 ID。在公众平台线上模板库中选用模板获得
        data           是   模板消息数据
        url            否   链接地址
        mini_program   否   跳小程序所需数据, 如：`{'appid': 'appid', 'pagepath': 'index?foo=bar'}`
    """
    if app_id not in settings.WECHAT_APP_MAP:
        return

    data = data if (data and isinstance(data, dict)) else {}
    try:
        appsecret = settings.WECHAT_APP_MAP[app_id]['appsecret']
        session = RedisStorage(get_redis_connection())\
            if settings.CACHES['default']['BACKEND'] == 'django_redis.cache.RedisCache'\
                else MemoryStorage()
        client = WeChatClient(app_id, appsecret, session=session)

        return client.message.send_template(
            touser, template_id, data, url=url, mini_program=mini_program
        )
    except Exception as e:
        logger.error(f'mp_send_template_error:{e}')
