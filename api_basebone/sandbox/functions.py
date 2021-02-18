# 沙箱中可用的方法
from api_basebone.services import queryset as queryset_service
from django.apps import apps


def get_queryset(request, model):
    """获取指定的模型查询结果集，在此之上可以继续进行filter操作。
    """
    if isinstance(model, str) and '__' in model:
        seg = model.split('__')
        model = apps.get_model(seg[0], seg[1])
    return queryset_service.queryset(request, model)


context = {
    'get_queryset': get_queryset
}