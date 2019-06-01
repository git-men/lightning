import operator
from functools import reduce

from django.apps import apps
from django.db.models import Manager, Q
from django.template import engines

django_engine = engines['django']

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
    "isnull": "__isnull",
}


def get_expression_value(item, context):
    """获取表达式的值"""
    object_key, attrs = None, None
    expression, expression_type = item.get('expression'), item.get('expression_type')
    if expression_type == 'object_attr':
        split_express = expression.split(".", 1)
        split_len = len(split_express)

        if split_len == 1:
            object_key = split_express[0]
        else:
            object_key, attrs = split_express

        if object_key not in context:
            raise Exception(f"context not include {object_key}")

        if split_len == 1:
            return context[object_key]
        # 这里不做任何异常的处理，如果有异常，则直接抛出
        value = getattr(context[object_key], attrs)
        if isinstance(value, Manager):
            return value.all()
    elif expression_type == 'queryset':
        model = item.get('model')
        if not model:
            raise Exception('model 不合法')
        model = apps.get_model(model)
        if not model:
            raise Exception('model 不合法')

        split_express = expression.split("=", 1)
        field_key, template = split_express
        filter_kwargs = {
            field_key: django_engine.from_string(template).render(context=context)
        }
        return model.objects.filter(**filter_kwargs)
    return value


def build_filter_conditions(filters, context=None):
    """构造过滤器

    Params:
        filters list 包含字典的列表数据

        数据示例：
            [
                {
                    field: xxxx,
                    operator: xxxx,
                    value: xxxx,
                }
            ]
    """
    if not filters or not isinstance(filters, list):
        return None, None

    if not isinstance(context, dict):
        context = {}

    valid_keys = {"field", "operator"}
    trans_cons, exclude_cons = [], []

    for item in filters:
        if not isinstance(item, dict) or not valid_keys.issubset(set(item.keys())):
            continue

        item_value = item.get("value")
        if "expression" in item:
            try:
                item_value = get_expression_value(item, context)
            except Exception:
                continue

        if item["operator"] in ["!=", "!==", "<>"]:
            exclude_cons.append(Q(**{item["field"]: item_value}))
        else:
            operate = OPERATOR_MAP.get(item["operator"], "")
            field = item["field"]
            key = f"{field}{operate}"
            trans_cons.append(Q(**{key: item_value}))

    return (
        reduce(operator.and_, trans_cons) if trans_cons else None,
        reduce(operator.and_, exclude_cons) if exclude_cons else None,
    )


def get_valid_conditions(filters):
    """获取合法的过滤条件

    Params:
        filters list 包含字典的列表数据

        数据示例：
            [
                {
                    field: xxxx,
                    operator: xxxx,
                    value: xxxx,
                }
            ]

    Returns:
        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx,
            },
            ...
        ]
    """
    result = {}
    valid_keys_normal = {"field", "operator", "value"}
    valid_keys_expression = {"field", "operator", "expression"}
    if not filters or not isinstance(filters, list):
        return result

    for item in filters:
        if isinstance(item, dict) and item.get("field"):
            temp_set_keys = None
            if valid_keys_normal.issubset(set(item.keys())):
                temp_set_keys = valid_keys_normal
            elif valid_keys_expression.issubset(set(item.keys())):
                temp_set_keys = valid_keys_expression

            if temp_set_keys:
                temp_key = item["field"]
                if temp_key not in result:
                    result[temp_key] = item
    return result
