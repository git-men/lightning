import inspect
import types
from functools import wraps

from django.apps import apps
from django.db.models.fields import DateTimeField

from .query import QuerySetExtend
from .fields import DateTimeFieldExtend


def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(*args, **kwargs)

        setattr(cls, func.__name__, wrapper)
        return func

    return decorator


def extend_objects(queryset_class):
    """
    迭代扩展查询方法
    """

    for name, method in inspect.getmembers(queryset_class, predicate=inspect.isfunction):
        for model in apps.get_models():
            setattr(model.objects, name, types.MethodType(method, model.objects))


def extend_method(origin_class, extend_class):

    for name, method in inspect.getmembers(extend_class, predicate=inspect.isfunction):
        setattr(origin_class, name, method)


extend_objects(QuerySetExtend)
extend_method(DateTimeField, DateTimeFieldExtend)
