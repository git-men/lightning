import re
import json
import operator
from decimal import Decimal
from functools import reduce
from django.utils import timezone
from django.db.models import F, Value, Count, Sum, Avg, Max, Min, StdDev, Variance
from django.db.models.functions import Concat


def reduce_wrap(func):
    return lambda *args: reduce(func, args)


def cmp_wrap(func):
    return lambda *args: bool(reduce(lambda a, b: a is not False and func(a, b) and b, args))


FUNCS = {
    'round': round,
    '__getattr__': getattr,
    'now': timezone.now,
    'today': lambda: timezone.now().date(),
    'max': max,
    'min': min,
    'add': reduce_wrap(operator.add),
    'sub': reduce_wrap(operator.sub),
    'mul': reduce_wrap(operator.mul),
    'div': reduce_wrap(operator.truediv),
    'mod': reduce_wrap(operator.mod),
    'pow': reduce_wrap(operator.pow),
    'and': lambda *args: all(args),
    'or': lambda *args: any(args),
    'len': len,
    'decimal': Decimal,
    'lt': cmp_wrap(operator.lt),
    'lte': cmp_wrap(operator.le),
    'gt': cmp_wrap(operator.gt),
    'gte': cmp_wrap(operator.ge),
    'eq': cmp_wrap(operator.eq),
    'not': operator.not_,
    'getitem': operator.getitem,
    'contains': lambda container, *args: all(k in container for k in args),
    'if': lambda cond, a, b: a if cond else b,
    'slice': lambda obj, *args: obj[slice(*args)],
    'F': F,
    'Concat': Concat,
    'Value': Value,
    'Count': Count,
    'Sum': Sum,
    'Avg': Avg,
    'Max': Max,
    'Min': Min,
    'StdDev': StdDev,
    'Variance': Variance
}


def split_expression(expression, symbol):
    quote = False
    surround = 0
    buffer = ''
    escape = False
    for char in expression:
        if escape and quote:
            escape = False
        else:
            if char == symbol:
                if surround == 0 and not quote:
                    yield buffer
                    buffer = ''
                    continue
            elif char == '\\':
                if quote:
                    escape = True
            elif char == '"':
                quote = not quote
            elif char in '([{':
                surround += 1
            elif char in ')]}':
                surround -= 1
        buffer += char
    if buffer:
        yield buffer


def resolve_expression(expression, variables=None):
    expression = expression.strip()

    try:
        return json.loads(expression)
    except json.JSONDecodeError:
        pass

    matched = re.match('^(\w+)\((.*)\)$', expression)
    if matched:
        func, arg_str = matched.groups()
        if func == '__variables__':
            return variables
        args = [resolve_expression(buffer, variables=variables) for buffer in split_expression(arg_str, ',')]
        return FUNCS[func](*args)

    # 如果是常量字符串，直接当参数传回。    
    is_str = re.match(r'^(\'|\")(.*)(\'|\")$', expression)
    if is_str:
        return expression

    # 点操作符，getattr的语法糖
    exp = '__variables__()'
    for path_item in expression.split('.'):
        exp = f'__getattr__({exp}, "{path_item}")'
    return resolve_expression(exp, variables=variables)
