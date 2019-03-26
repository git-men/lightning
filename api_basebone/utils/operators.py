import operator

from functools import reduce
from django.db.models import Q

# 运算符映射
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
    "icontains": "__icontains",
    "between": "__range",
    "near": "__near",
    "has": "__has",
    "has_any": "__has_any",
    "has_all": "__has_all",
}


def build_filter_conditions(filters):
    """构造过滤器
    """

    assert isinstance(filters, list), 'filters 应该是一个列表的数据结构'
    if not filters:
        return None, None

    trans_cons = []
    exclude_cons = []
    for item in filters:
        if (item['operator'] in ['!=', '!==', '<>']):
            exclude_cons.append(Q(**{item['field']: item['value']}))
        else:
            operate = OPERATOR_MAP.get(item['operator'], '')
            field = item['field']
            key = f'{field}{operate}'
            trans_cons.append(Q(**{key: item['value']}))

    return reduce(operator.and_, trans_cons) if trans_cons else None, reduce(operator.and_, exclude_cons) if exclude_cons else None
