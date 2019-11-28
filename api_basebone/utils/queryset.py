from django.db.models.query import QuerySet, Prefetch
from django.db.models import Manager
from .operators import build_filter_conditions2
from ..export.fields import get_attr_in_gmeta_class
from ..core import gmeta
from ..restful.serializers import multiple_create_serializer_class, get_field

__all__ = ['filter', 'serialize', 'annotate']


def filter_queryset(queryset, filters=None):
    if not filter:
        return queryset
    cons = build_filter_conditions2(filters)
    if cons:
        queryset = queryset.filter(cons)
    # if exclude:
    #     queryset = queryset.exclude(exclude)
    # cons, exclude = build_filter_conditions(filters)
    # if cons:
    #     queryset = queryset.filter(cons)
    # if exclude:
    #     queryset = queryset.exclude(exclude)

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

    if field.one_to_one:
        return field.remote_field.name, field
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
                result = get_relation_field_related_name(
                    field.related_model, field.remote_field.name
                )
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
        model, expand_fields, action=action
    )
    serializer = serializer_class(data, many=many)
    return serializer.data


def annotate_queryset(queryset, fields=None, context=None):
    annotated_fields = get_attr_in_gmeta_class(queryset.model, gmeta.GMETA_ANNOTATED_FIELDS, {})
    if fields is not None:
        annotated_fields = {k: v for k, v in annotated_fields.items() if k in fields}
    if annotated_fields:
        return queryset.annotate(**{name: field['annotation'] if not callable(field['annotation']) else field['annotation'](context or {}) for name, field in annotated_fields.items()})
    return queryset


def expand_dict_to_prefetch(model, expand_dict, fields=None, context=None):
    result = []
    for key, value in expand_dict.items():
        field = get_field(model, key)
        next_model = field.related_model
        next_fields = fields and [field.split('.', maxsplit=1)[-1] for field in fields if field.startswith(key+'.')]
        pfs = expand_dict_to_prefetch(next_model, value, fields=next_fields, context=context)
        # if not pfs:
        # 是否能节省资源？
        #     result.append(key)
        #     continue
        qs = next_model.objects.prefetch_related(*pfs)
        prefetch = Prefetch(key, queryset=annotate_queryset(qs, fields=next_fields, context=context))
        result.append(prefetch)
    return result


# alias
filter = filter_queryset
serialize = serialize_queryset
annotate = annotate_queryset
