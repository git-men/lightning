from django.contrib.auth import get_user_model

from rest_framework import serializers
from api_basebone.utils import module


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta"""

    attrs = {
        'model': model,
    }

    if exclude_fields is not None and isinstance(exclude, (list, tuple)):
        attrs['exclude'] = exclude_fields
    else:
        attrs['fields'] = '__all__'

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
    """获取用户自定义的表单类"""

    action_map = {
        'create': 'Create',
        'update': 'Update',
    }

    form_module = module.get_admin_module(model._meta.app_config.name, module.BSM_FORM)
    class_name = '{}{}Form'.format(model.__name__, action_map[action])
    form = getattr(form_module, class_name, None)
    if form is None:
        return create_form_class(model, exclude_fields=exclude_fields, **kwargs)
    return form
