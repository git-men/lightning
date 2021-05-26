# 沙箱中可用的方法
from api_basebone.services import queryset as queryset_service
from api_basebone.core.exceptions import BusinessException
from django.apps import apps
from datetime import date
from api_basebone.sandbox.logger import LogCollector


__all__ = [
    'get_queryset', 'raise_error', 'get_model', 'today',
    'generate_sequence', 'get_logger', 'local_call_async',
    'call', 'call_async', 'push_wechat_notify'
]

get_model = apps.get_model
today = date.today

def generate_sequence(prefix, last, width):
    """生成序列号
    """
    current = str(last + 1).zfill(width)
    return '-'.join([prefix, today().strftime('%Y%m%d'), current])

def get_queryset(request, model, expand_fields=None):
    """获取指定的模型查询结果集，在此之上可以继续进行filter操作。
    """
    if isinstance(model, str) and '__' in model:
        seg = model.split('__')
        model = apps.get_model(seg[0], seg[1])
    return queryset_service.queryset(request, model, expand_fields=expand_fields)

def raise_error(message, code='9999', data=None, app=None):
    raise BusinessException(error_code=code, error_message=message, error_data=data, error_app=app)


def get_logger(name):
    """每次调用，都是一个新的
    """
    return LogCollector(name)


def local_call_async(func_obj, params={}):
    from lightning_task.tasks import _execute_async
    return _execute_async.delay(func_obj, params)

def call(db_func, params={}, develop_mode=False):
    from lightning_code.tasks import call_function
    return call_function(db_func, params, develop_mode)

def call_async(db_func, params={}, develop_mode=False):
    # TODO 检测是否有开启异步
    from lightning_code.tasks import call_function
    return call_function.delay(db_func, params, develop_mode)

def push_wechat_notify(robot, message, mentioned_mobiles=[], delay=True):
    from api_basebone.tasks import wechat_robot_push
    if delay:
        return wechat_robot_push.delay(robot, message, mentioned_mobiles)
    return wechat_robot_push(robot, message, mentioned_mobiles)

context = {
    'get_queryset': get_queryset,
    'get_model': get_model,
    'raise_error': raise_error
}