# 沙箱中可用的方法
from api_basebone.services import queryset as queryset_service
from api_basebone.core.exceptions import BusinessException
from django.apps import apps

__all__ = ['get_queryset', 'raise_error', 'get_model']

get_model = apps.get_model

def get_queryset(request, model):
    """获取指定的模型查询结果集，在此之上可以继续进行filter操作。
    """
    if isinstance(model, str) and '__' in model:
        seg = model.split('__')
        model = apps.get_model(seg[0], seg[1])
    return queryset_service.queryset(request, model)

def raise_error(message, code='9999', data=None, app=None):
    raise BusinessException(error_code=code, error_message=message, error_data=data, error_app=app)


context = {
    'get_queryset': get_queryset,
    'get_model': get_model,
    'raise_error': raise_error
}