"""
涉及到 model._meta 相关的工具方法
"""

import importlib
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields import NOT_PROVIDED

from api_basebone.core.admin import BSMAdminModule


def get_concrete_fields(model):
    return [
        item
        for item in model._meta.get_fields()
        if item.concrete
    ]


def get_related_model_field(model, related_model):
    """
    model 中的关系字段是否指向 related_model

    例如，文章 Article 中的有一个字段
    """
    for f in model._meta.get_fields():
        if f.is_relation and f.concrete:
            if f.related_model is related_model:
                return f


def get_relation_field(model, field_name):
    """获取字段引用的模型"""
    try:
        field = model._meta.get_field(field_name)

        if field.is_relation and field.concrete:
            return field
    except Exception:
        return


def get_relation_field_related_name(model, field_name):
    """获取关系字段的 related_name"""
    field = get_relation_field(model, field_name)
    if not field:
        return

    related_name = field.remote_field.related_name
    if related_name is None:
        return '{}_set'.format(model.__name__.lower()), field
    return related_name, field


def get_field_default_value(field):
    """
    TODO: 需要检测 default 是否是函数
    """
    if field.default is NOT_PROVIDED:
        if field.null:
            return None
        else:
            raise Exception('this field has not default value')
    return field.default


def tree_parent_field(model, field_name):
    """获取树形字段数据

    Returns:
        （字段名，related_name, 默认值)
    """
    related_name, field = get_relation_field_related_name(model, field_name)
    if not related_name:
        return

    try:
        default_value = get_field_default_value(field)
        return (field_name, related_name, default_value)
    except Exception:
        return


def get_export_apps():
    """获取导出配置的 app"""
    apps = getattr(settings, 'BSM_EXPORT_APPS', None)
    if apps and isinstance(apps, list):
        return apps
    return ['auth'] + settings.INTERNAL_APPS


def get_bsm_app_admin(app_label):
    """获取 BSM 应用的 admin"""
    try:
        return importlib.import_module(f'{app_label}.bsm.admin')
    except Exception as e:
        return


def get_bsm_model_admin(model):
    """获取 BSM Admin 模块"""
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    return BSMAdminModule.modules.get(key)


def load_custom_admin_module():
    """加载符合约定的 admin 的 module"""
    export_apps = get_export_apps()
    if not export_apps:
        return
    for app_label in export_apps:
        get_bsm_app_admin(app_label)


def get_custom_form_module(model):
    """获取用户自定义的表单模块

    TODO: 暂时应用下面的不能写入到其他应用下面
    """
    try:
        return importlib.import_module(f'{app_label}.bsm.forms')
    except Exception:
        return
