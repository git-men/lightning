from django.db.models.query import QuerySet
from django.db.models import Manager
from .operators import build_filter_conditions
from ..restful.serializers import multiple_create_serializer_class


__all__ = ['filter', 'serialize']


def filter_queryset(queryset, filters=None):
    if not filter:
        return queryset
    cons, exclude = build_filter_conditions(filters)
    if cons:
        queryset = queryset.filter(cons)
    if exclude:
        queryset = queryset.exclude(exclude)

    return queryset


def check_field_is_reverse(field):
    """检测字段是否是反向字段 """
    return field.is_relation and field.auto_created and not field.concrete


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


def translate_expand_fields(_model, expand_fields):
    """转换展开字段"""
    for out_index, item in enumerate(expand_fields):
        field_list = item.split('.')
        model = _model
        for index, value in enumerate(field_list):
            field = model._meta.get_field(value)
            if check_field_is_reverse(field):
                result = get_relation_field_related_name(field.related_model, field.remote_field.name)
                if result:
                    field_list[index] = result[0]
            if field.is_relation:
                model = field.related_model
        expand_fields[out_index] = '.'.join(field_list)
    return expand_fields


def serialize_queryset(data, action='list', expand_fields=None):
    if isinstance(data, QuerySet) or isinstance(data, Manager):
        model = data.model
        many = True
    else:
        model = data.__class__
        many = False

    if expand_fields is None:
        expand_fields = []
    else:
        expand_fields = translate_expand_fields(model, expand_fields)
        pass
    serializer_class = multiple_create_serializer_class(
        model, expand_fields, action=action,
    )
    serializer = serializer_class(data, many=many)
    return serializer.data


# alias
filter = filter_queryset
serialize = serialize_queryset
