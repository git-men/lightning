"""
涉及到 model._meta 相关的工具方法
"""

from django.contrib.auth import get_user_model
from django.db.models.fields import NOT_PROVIDED


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
