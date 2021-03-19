import types
from django.db.models.query import QuerySet, Prefetch
from django.db.models import Manager

from .operators import build_filter_conditions2
from ..export.fields import get_attr_in_gmeta_class
from ..core import gmeta
from ..restful.serializers import multiple_create_serializer_class, get_field, nested_display_fields, \
    sort_expand_fields, display_fields_to_expand_fields
from ..services.expresstion import resolve_expression

__all__ = ['filter', 'serialize', 'annotate', 'GManager', 'BSMQuerySet']


def filter_queryset(queryset, filters=None, context=None):
    if not filter:
        return queryset
    cons = build_filter_conditions2(filters, context=context)
    if cons:
        queryset = queryset.filter(cons)

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


class ChainProxy:
    def __init__(self, queryset, annotations):
        self.origin_chain = types.MethodType(type(queryset)._chain, queryset)
        self.annotations = annotations

    def __call__(self, *args, **kwargs):
        clone = self.origin_chain(*args, **kwargs)
        clone.query.resolve_ref = ResolveRefProxy(clone.query, self.annotations)
        return clone


class ResolveRefProxy:
    def __init__(self, query, annotations):
        self.query = query
        self.origin_resolve_ref = types.MethodType(type(query).resolve_ref, query)
        self.annotations = annotations

    def __call__(self, name, allow_joins=True, reuse=None, summarize=False, simple_col=False):
        if name in self.annotations:
            return self.annotations[name].resolve_expression(self.query, allow_joins=True, reuse=None, summarize=summarize)
        return self.origin_resolve_ref(name, allow_joins=True, reuse=None, summarize=False, simple_col=False)


def get_real_model(fake_model):
    """为了适配meta里模型可能为fake的情况"""
    from django.apps import apps
    return apps.get_model(fake_model._meta.app_label, fake_model._meta.model_name)


def annotate_queryset(queryset, fields=None, context=None):
    annotated_fields = {}
    real_model = get_real_model(queryset.model)
    if 'GMeta' in real_model.__dict__:
        # 这样可以避免从继承过来的GMeta里取，对于one to one类型的继承来说会出错
        annotated_fields = getattr(real_model.__dict__['GMeta'], gmeta.GMETA_ANNOTATED_FIELDS, {})
    if fields is not None:
        annotated_fields = {k: v for k, v in annotated_fields.items() if k in fields}
    if annotated_fields:
        annotations = {name: field['annotation'] for name, field in annotated_fields.items()}
        for name, annotation in annotations.items():
            if callable(annotation):
                annotations[name] = annotation(context or {})
        queryset._chain = ChainProxy(queryset, annotations)
        queryset = queryset.annotate(**annotations)
    return queryset


def expand_dict_to_prefetch(model, expand_dict=None, fields=None, context=None, display_fields=None):
    result = []
    if expand_dict is None:
        if display_fields is not None:
            expand_dict = sort_expand_fields(display_fields_to_expand_fields(display_fields))
        else:
            expand_dict = {}

    for key, value in expand_dict.items():
        field = get_field(model, key)
        next_model = field.related_model
        next_fields = fields and [field.split('.', maxsplit=1)[-1] for field in fields if field.startswith(key+'.')]
        nested = nested_display_fields(model, display_fields, key)
        if nested is not None and not field.concrete:
            nested.append(field.field.name)
        pfs = expand_dict_to_prefetch(next_model, value, fields=next_fields, context=context, display_fields=nested)
        # if not pfs:
        # 是否能节省资源？
        #     result.append(key)
        #     continue
        qs = next_model.objects.defer(*get_exclude_fields_by_model(next_model)).prefetch_related(*pfs)
        if display_fields is not None and nested:
            qs = queryset_only(qs, nested)
        # 使关联关系也能用annotated_field
        prefetch = Prefetch(key, queryset=annotate_queryset(qs, fields=next_fields, context=context))
        result.append(prefetch)
    return result


def get_exclude_fields_by_model(model):
    if not hasattr(model, 'GMeta'):
        return []
    return getattr(model.GMeta, gmeta.GMETA_SERIALIZER_EXCLUDE_FIELDS, [])


def queryset_only(queryset, display_fields):
    real_model = get_real_model(queryset.model)
    annotated_fields = get_attr_in_gmeta_class(real_model, gmeta.GMETA_ANNOTATED_FIELDS, {})
    computed_fields = get_attr_in_gmeta_class(real_model, gmeta.GMETA_COMPUTED_FIELDS, [])
    computed_field_names = {c['name'] for c in computed_fields}
    only = [d for d in display_fields if '.' not in d and d not in annotated_fields and d not in computed_field_names]
    for d in display_fields:
        if '.' in d:
            field = get_field(queryset.model, d.split('.')[0])
            if field:
                if field.concrete:
                    only.append(field.name)

    for c in computed_fields:
        only += c.get('deps', [])
    if '*' in only:
        return queryset
    only.append('pk')
    return queryset.only(*only)


def queryset_prefetch(queryset, expand_dict=None, context=None, display_fields=None):
    if display_fields is not None:
        queryset = queryset_only(queryset, display_fields)
    return queryset.defer(*get_exclude_fields_by_model(queryset.model)).prefetch_related(
        *expand_dict_to_prefetch(
            queryset.model, expand_dict, context=context, display_fields=display_fields,
        )
    )


# alias
filter = filter_queryset
serialize = serialize_queryset
annotate = annotate_queryset
only = queryset_only


# 尚未完全能用，prefetch有问题
# class GMIterable(ModelIterable):
#     def __iter__(self):
#         serializer_class = self.queryset._serializer_class
#         for obj in super().__iter__():
#             return serializer_class(obj).data


class BSMQuerySet(QuerySet):
    def render(self, display_fields):
        # clone = queryset_prefetch(self, display_fields=display_fields)
        # clone._iterable_class = GMIterable
        # clone._serializer_class = multiple_create_serializer_class(
        #     clone.model,
        #     expand_fields=display_fields_to_expand_fields(display_fields),
        #     display_fields=display_fields,
        #     action='retrieve',
        # )
        # return clone
        serializer_class = multiple_create_serializer_class(
            self.model,
            display_fields=display_fields,
            action='list',
        )
        qs = queryset_prefetch(self, display_fields=display_fields)
        return serializer_class(qs.all(), many=True).data

    def render_get(self, display_fields, **conditions):
        serializer_class = multiple_create_serializer_class(
            self.model,
            display_fields=display_fields,
            action='retrieve',
        )
        qs = queryset_prefetch(self, display_fields=display_fields)
        return serializer_class(qs.get(**conditions)).data

    def annotate_fields(self, fields=None, context=None):
        return annotate_queryset(self, fields=fields, context=context)

    # def _chain(self):
    #     c = super()._chain()
    #     if hasattr(self, '_serializer_class'):
    #         c._serializer_class = self._serializer_class
    #     return c


GManager = Manager.from_queryset(BSMQuerySet)
