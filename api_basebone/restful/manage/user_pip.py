"""
数据的操作

通过一系列的操作，对数据进行清洗
"""
from functools import partial

from django.contrib.auth import get_user_model

from api_basebone.core import admin, gmeta
from api_basebone.utils import meta
from api_basebone.utils.gmeta import get_gmeta_config_by_key


def insert_user_info(data, model, user_id, action):
    if not isinstance(data, dict):
        return []

    creator_field = get_gmeta_config_by_key(model, gmeta.GMETA_CREATOR_FIELD)
    updater_field = get_gmeta_config_by_key(model, gmeta.GMETA_UPDATER_FIELD) or getattr(model, admin.BSM_AUTH_FILTER_FIELD, None)
    result = [creator_field, updater_field]

    if updater_field:
        data[updater_field] = user_id
    if action == 'create' and creator_field and creator_field != updater_field:
        data[creator_field] = user_id
    for field in model._meta.get_fields():
        if hasattr(field, 'get_bsm_internal_type'):
            if field.get_bsm_internal_type() == 'UserField':
                update_insert = action == 'update' and field.auto_current
                create_insert = action == 'create' and (field.auto_current or field.auto_current_add)
                # 更新时只有auto_current的字段需要插入，创建时则无论是auto_current还是auto_current_add的字段都插入
                if update_insert or create_insert:
                    data[field.name] = user_id
                    print(data)
                    result.append(field.name)

    return result


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

    #  这里兼容签名方式
    if view.request.user.is_anonymous:
        return

    model_name, model = view.model_slug, view.model

    # 第一部分，先检测模型中的字段是否有引用用户模型，如果有，则注入用户数据

    user = get_user_model().objects.get(id=view.request.user.id)
    insert_user = partial(insert_user_info, user_id=user.id, action=view.action)

    auth_fields = insert_user(data, model)

    relation_fields = meta.get_all_relation_fields(model)
    if relation_fields:
        for item in relation_fields:
            if item.name not in data or item.name in auth_fields:
                # 如果字段没有在 data 中或者字段名称和 auth_fields 相同，则不做任何处理
                continue

            value = data[item.name]

            if meta.check_field_is_reverse(item):
                # FIXME:  当前反向字段使用的是列表数据结构
                if not value or not isinstance(value, list):
                    continue

                for reverse_item in value:
                    insert_user(reverse_item, item.related_model)
            else:
                # 这里说明是正向字段
                if item.many_to_many:
                    # 说明是多对多字段
                    if not value or not isinstance(value, list):
                        continue

                    for child_item in value:
                        insert_user(child_item, item.related_model)
                else:
                    # 使用字典数据结构
                    if isinstance(value, dict):
                        insert_user(value, item.related_model)
    return data
