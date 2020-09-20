"""
涉及到 model._meta 相关的工具方法
"""

from django.apps import apps
from django.conf import settings
from django.db.models.fields import NOT_PROVIDED

from api_basebone.core.admin import BSMAdminModule
from api_basebone.utils import module


def get_reverse_fields(model):
    """获取模型的反向字段"""
    return [
        item
        for item in model._meta.get_fields()
        if item.auto_created and not item.concrete
    ]


def get_all_relation_fields(model):
    """获取模型中所有的关系字段"""
    return [item for item in model._meta.get_fields() if item.is_relation]


def check_field_is_reverse(field):
    """检测字段是否是反向字段 """
    return field.is_relation and field.auto_created and not field.concrete


def get_field_by_reverse_field(field):
    """获取字段，通过反转字段

    例如 product 引用了 User，通过 User 的反转字段查找到 product 中对应的字段
    """
    return field.remote_field


def get_concrete_fields(model):
    return [item for item in model._meta.get_fields() if item.concrete]


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

    if field.one_to_one:
        return field.remote_field.name, field
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
    if hasattr(settings, 'BSM_EXPORT_APPS'):
        export_apps = settings.BSM_EXPORT_APPS
    else:
        export_apps = list(apps.app_configs.keys())

    if hasattr(settings, 'BSM_EXPORT_APPS_EXCLUDE'):
        export_apps = [e for e in export_apps if e not in settings.BSM_EXPORT_APPS_EXCLUDE]

    return export_apps


def get_bsm_model_admin(model):
    """获取 Admin 类"""
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    return BSMAdminModule.modules.get(key)


def load_custom_admin_module():
    """加载符合约定的 admin 的 module"""
    export_apps = get_export_apps()
    if not export_apps:
        return

    for app_label in export_apps:
        app = apps.get_app_config(app_label)
        module.get_admin_module(app.name, module.BSM_ADMIN)


def get_dict_expand_fields_by_level(model, level):
    """根据 level 获取展开的字段

    Params:
        model class  django 模型类
        level int 层级

    Returns:
        list
    """
    assert isinstance(level, int), 'level 应该是整型的数字'
    if level <= 0:
        return {}
    relation_fields = get_all_relation_fields(model)
    if not relation_fields:
        return {}

    result = {}
    for item in relation_fields:
        result[item.name] = get_dict_expand_fields_by_level(item.related_model, level - 1)
    return result


def expand_fields_to_list(field_dict, parent=None, result=None):
    """
    字典型的展开字段数据转换为列表
    """
    if result is None:
        result = []

    if not field_dict:
        return

    for key, value in field_dict.items():
        temporary_parent = f'{parent}.{key}' if parent else key

        if not value:
            result.append(temporary_parent)
        else:
            expand_fields_to_list(value, parent=temporary_parent, result=result)
    return result


def get_expand_fields_by_level(model, level):
    """获取模型指定层数的展开字段

    Params:
        model class django 模型类
        level int 展开字段的层数

    Returns:
        list
    """
    fields = get_dict_expand_fields_by_level(model, level)
    result = []
    if not fields:
        return
    for key, value in fields.items():
        item_expands = expand_fields_to_list({key: value})
        result += item_expands
    return result


def get_model_gmeta_class(model):
    """
    获取模型的 GMeta 类
    """
    return getattr(model, 'GMeta')


def get_model_gmeta_config(model, config_key):
    """
    获取模型的 GMeta 类中指定键的配置
    """
    gmeta_class = get_model_gmeta_class(model)
    if not gmeta_class:
        return

    return getattr(gmeta_class, config_key)


def get_accessor_name(field):
    """
    反向字段获取 accessor name

    TAG: 元工具函数
    """
    return field.get_accessor_name()
