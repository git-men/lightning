from django.contrib.auth import get_user_model

from rest_framework import serializers
from api_basebone.utils.meta import get_custom_form_module


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta"""

    attrs = {
        'model': model,
        'fields': '__all__'
    }
    if exclude_fields is not None:
        attrs['exclude'] = exclude_fields

    return type('Meta', (object, ), attrs)


def create_form_class(model, exclude_fields=None, **kwargs):
    """构建序列化类"""

    attrs = {
        'Meta': create_meta_class(model, exclude_fields=None)
    }
    attrs.update(kwargs)

    class_name = f'{model}ModelSerializer'
    return type(
        class_name,
        (serializers.ModelSerializer, ),
        attrs
    )


def get_form_class(model, action, exclude_fields=None, **kwargs):
    """获取表单类"""

    action_map = {
        'create': 'Create',
        'update': 'Update',
    }

    module = get_custom_form_module(model)
    class_name = '{}{}Form'.format(model.__name__, action_map[action])
    form = getattr(module, class_name, None)
    return create_form_class(model, exclude_fields=exclude_fields, **kwargs) if form is None else form
