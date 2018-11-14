"""
涉及到 model._meta 相关的工具方法
"""

import importlib
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields import NOT_PROVIDED

from api_basebone.core.admin import BSMAdminModule


def get_reverse_fields(model):
    """获取模型的反向字段"""
    return [
        item
        for item in model._meta.get_fields()
        if item.auto_created and not item.concrete
    ]


def get_field_by_reverse_field(field):
    """获取字段，通过反转字段

    例如 product 引用了 User，通过 User 的反转字段查找到 product 中对应的字段
    """
    model = field.related_model
    relation_fields = [
        item for item in get_concrete_fields(model)
        if item.is_relation and field.model is item.related_model and field.model is not item.model
    ]

    if not relation_fields:
        return
    if len(relation_fields) == 1:
        return relation_fields[0]

    # 如果一个模型引用一个模型多次，这时候需要根据 related_name 来进行判断
    fields_map = {}
    for item in relation_fields:
        related_name = item.remote_field.related_name
        if related_name is None:
            related_name = item.model._meta.model_name
        fields_map[related_name] = item
    return fields_map.get(field.name)


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


def get_relation_field(model, field_name, reverse=False):
    """获取模型指定名称的关系字段

    Params:
        model 模型类
        field_name 字段名
        reverse bool 是否包含反向的关系字段

    Returns:
        field object 字段对象
    """
    try:
        field = model._meta.get_field(field_name)
        if not field.is_relation:
            return

        if reverse:
            return field
        elif field.concrete:
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
