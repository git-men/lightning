from .meta import get_all_relation_fields


def hand_signle_export_field_to_prefetch(model, field):
    """根据单个导出字段，筛选出 prefetch 的字段列表"""
    prefetch_list = []
    inner_model = model

    field_split = field.split('.')
    for inner_item in field_split:
        relation_fields = [item.name for item in get_all_relation_fields(inner_model)]

        if inner_item in relation_fields:
            prefetch_list.append(inner_item)
            inner_model = inner_model._meta.get_field(inner_item).related_model

    if len(prefetch_list):
        return '.'.join(prefetch_list)


def get_prefetch_fields_from_export_fields(model, fields=None):
    """
    从导出配置中获取 prefetch 字段，针对的是 v2 版本
    """
    prefetch_set = set()

    for item in fields:
        field_str = item[0] if isinstance(item, list) else item
        prefetch_field = hand_signle_export_field_to_prefetch(model, field_str)

        if prefetch_field:
            prefetch_set.add(prefetch_field)
    return list(prefetch_set)
