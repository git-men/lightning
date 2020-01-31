"""
数据的操作

通过一系列的操作，对数据进行清洗
"""
from django.contrib.auth import get_user_model

from api_basebone.core import gmeta
from api_basebone.utils import meta
from api_basebone.utils.gmeta import get_gmeta_config_by_key


def insert_user_to_data(model, user, data):
    """插入用户到数据中"""

    # 第一部分，先检测模型中的字段是否有引用用户模型，如果有，则注入用户数据
    auth_user_field = None

    # 检测模型中是否有字段引用了用户模型
    has_user_field = meta.get_related_model_field(model, get_user_model())
    if has_user_field:
        field_name = get_gmeta_config_by_key(model, gmeta.GMETA_CLIENT_USER_FIELD)
        if field_name:
            auth_user_field = field_name
            # 如果用户数据中没有传递用户的数据，则进行插入
            if field_name not in data:
                data[field_name] = user.id

    relation_fields = meta.get_all_relation_fields(model)
    if relation_fields:
        for item in relation_fields:
            if item.name not in data or item.name == auth_user_field:
                # 如果字段没有在 data 中或者字段名称和 auth_user_field 相同，则不做任何处理
                continue

            value = data[item.name]

            if meta.check_field_is_reverse(item):
                # FIXME:  当前反向字段使用的是列表数据结构
                if not value or not isinstance(value, list):
                    continue

                has_user_field = meta.get_related_model_field(
                    item.related_model, get_user_model()
                )
                if has_user_field:
                    field_name = get_gmeta_config_by_key(
                        item.related_model, gmeta.GMETA_CLIENT_USER_FIELD
                    )
                    if field_name:
                        for reverse_item in value:
                            if isinstance(reverse_item, dict):
                                # 如果用户数据中没有传递用户的数据，则进行插入
                                if field_name not in reverse_item:
                                    reverse_item[field_name] = user.id
            else:
                # 这里说明是正向字段
                if item.many_to_many:
                    # 说明是多对多字段
                    if not value or not isinstance(value, list):
                        continue

                    has_user_field = meta.get_related_model_field(
                        item.related_model, get_user_model()
                    )
                    if has_user_field:
                        field_name = get_gmeta_config_by_key(
                            item.related_model, gmeta.GMETA_CLIENT_USER_FIELD
                        )
                        if field_name:
                            for child_item in value:
                                if isinstance(child_item, dict):
                                    # 如果用户数据中没有传递用户的数据，则进行插入
                                    if field_name not in child_item:
                                        child_item[field_name] = user.id
                else:
                    # 使用字典数据结构
                    if isinstance(value, dict):
                        has_user_field = meta.get_related_model_field(
                            item.related_model, get_user_model()
                        )
                        if has_user_field:
                            field_name = get_gmeta_config_by_key(
                                item.related_model, gmeta.GMETA_CLIENT_USER_FIELD
                            )
                            if field_name:
                                # 如果用户数据中没有传递用户的数据，则进行插入
                                if field_name not in value:
                                    value[field_name] = user


def add_login_user_data(view, data):
    """
    给数据添加上用户数据

    对于字段，这里分：正向的关系字段，反向的关系字段
    """
    if view.request.method.upper() in ['GET', 'OPTIONS', 'DELETE']:
        return

    if view.action not in ['create', 'update', 'partial_update']:
        return

    if not view.request.data:
        return

    user = get_user_model().objects.filter(id=view.request.user.id).first()
    if user:
        return insert_user_to_data(view.model, user, data)
