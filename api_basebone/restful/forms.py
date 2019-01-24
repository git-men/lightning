from rest_framework import serializers

from api_basebone.utils import module
from api_basebone.restful.const import MANAGE_END_SLUG, CLIENT_END_SLUG


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta 类"""
    attrs = {
        'model': model,
    }

    if exclude_fields is not None and isinstance(exclude_fields, (list, tuple)):
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
        class_name, (serializers.ModelSerializer, ), attrs
    )


def get_form_class(model, action, exclude_fields=None, end=MANAGE_END_SLUG, **kwargs):
    """获取用户自定义的表单类

    Params:
        model class 模型类
        action string 方法名
        exclude_fields list or tuple 排除的字段
        end string 端，指定是哪个端，有客户端和管理端

    Returns:
        class 表单类
    """

    name_suffix_map = {
        MANAGE_END_SLUG: 'ManageForm',
        CLIENT_END_SLUG: 'ClientForm',
    }

    action_map = {
        'create': 'Create',
        'update': 'Update',
    }

    form_module = module.get_admin_module(model._meta.app_config.name, module.BSM_FORM)

    name_suffix = name_suffix_map.get(end)
    if not name_suffix:
        return create_form_class(model, exclude_fields=exclude_fields, **kwargs)

    class_name = '{}{}{}'.format(model.__name__, action_map[action], name_suffix)
    form_class = getattr(form_module, class_name, None)
    if form_class is None:
        return create_form_class(model, exclude_fields=exclude_fields, **kwargs)
    return form_class
