"""
这里是处理模型中 GMeta 中的业务逻辑
"""

from django.contrib.auth import get_user_model
from api_basebone.core import gmeta as gmeta_const
from .meta import get_concrete_fields


def get_gmeta_class(model):
    """
    获取模型的 GMeta 类
    """
    return getattr(model, 'GMeta', None)


def get_gmeta_pure_config(model, config_key):
    """
    获取模型的 GMeta 类中指定键的配置

    这个方法只是粗糙的获取配置，没有做任何的校验，所以这个方法获取
    到的配置不一定是合法的
    """
    gmeta_class = get_gmeta_class(model)
    if not gmeta_class:
        return

    return getattr(gmeta_class, config_key, None)


def get_gmeta_client_user_field(model, config_key):
    """
    获取用户字段的配置
    """
    user_field_name = get_gmeta_pure_config(model, config_key)
    if not user_field_name:
        return

    field_name_map = {item.name: item for item in get_concrete_fields(model)}
    user_filed = field_name_map.get(user_field_name)

    # 如果获取的字段为空或者获取到字段的关系模型不是 User，则返回 None
    if not user_filed or user_filed.related_model is not get_user_model():
        return
    return user_field_name


def get_gmeta_config_by_key(model, config_key):
    """
    获取模型的 GMeta 类中指定键的配置

    这个方法获取到的配置，是经过校验过的配置，可以放心使用
    """

    handler_map = {gmeta_const.GMETA_CLIENT_USER_FIELD: get_gmeta_client_user_field}
    handler = handler_map.get(config_key)
    if handler:
        return handler(model, config_key)
    return get_gmeta_pure_config(model, config_key)


def get_attr_in_gmeta_class(model, config_name, default_value=None):
    """获取指定模型 GMeta 类中指定的属性

    Params:
        model class django 模型类
        config_name string GMeta 类中配置项的名称
        default_value 任何数据类型 默认数据
    """

    gmeta_class = getattr(model, 'GMeta', None)
    if not gmeta_class:
        return default_value
    return getattr(gmeta_class, config_name, default_value)
