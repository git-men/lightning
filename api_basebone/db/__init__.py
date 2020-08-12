import inspect
import types

from django.apps import apps

from .query import QuerySetExtend


def extend_objects(queryset_class):
    """
    迭代扩展查询方法
    """

    for name, method in inspect.getmembers(queryset_class, predicate=inspect.isfunction):
        for model in apps.get_models():
            setattr(model.objects, name, types.MethodType(method, model.objects))


extend_objects(QuerySetExtend)
