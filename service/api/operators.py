import operator
from functools import reduce
from django.db.models import Q


OPERATOR_MAP = {
    ">": "__gt",
    ">=": "__gte",
    "<": "__lt",
    "<=": "__lte",
    "=": "",
    "in": "__in",
    "startswith": "__startswith",
    "endswith": "__endswith",
    "contains": "__contains",
    "between": "__range",
    "near": "__near",
    "has": "__has",
    "has_any": "__has_any",
    "has_all": "__has_all",
}


def build_filter_conditions(filters):
    """构造过滤器"""
    if not filters:
        return

    assert isinstance(filters, list), 'filters 应该是一个列表的数据结构'

    trans_cons = []
    for item in filters:
        operate = OPERATOR_MAP.get(item['operator'], '')
        field = item['field']
        key = f'{field}{operate}'
        trans_cons.append(Q(**{key: item['value']}))

    if trans_cons:
        return reduce(operator.and_, trans_cons)
