import re
import json
import logging
import operator
from decimal import Decimal
from functools import reduce
from django.utils import timezone
from django.db.models import *
from django.db.models.functions import Concat, Cast

log = logging.getLogger(__name__)


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
}


class BaseExpression:
    function_set = FUNCS

    @staticmethod
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

    def execute_function(self, function_name, arguments):
        args = [self.resolve(buffer) for buffer in arguments]
        log.debug(f'returning calling Fun: {function_name} with args: {args}')
        return self.function_set[function_name](*args)

    def resolve(self, expression):
        expression = expression.strip()

        try:
            return json.loads(expression)
        except json.JSONDecodeError:
            pass
        log.debug(f'resolving expression: {expression}')
        matched = re.match(r'^(\w+)\((.*)\)$', expression)
        if matched:
            func, arg_str = matched.groups()
            return self.execute_function(func, self.split_expression(arg_str, ','))

        raise NotImplementedError()


class Expression(BaseExpression):
    def __init__(self, variable_root):
        self.variable_root = variable_root

    def execute_function(self, function_name, arguments):
        if function_name == '__variable_root__':
            return self.variable_root
        return super().execute_function(function_name, arguments)

    def resolve(self, expression):
        try:
            return super().resolve(expression)
        except NotImplementedError:
            # 点操作符，getattr的语法糖
            exp = '__variable_root__()'
            for path_item in expression.split('.'):
                exp = f'__getattr__({exp}, "{path_item}")'
            log.debug(f'exp: {exp}')
            return self.resolve(exp)


DB_FUNC = {
    'F': F,
    'Concat': Concat,
    'Value': Value,
    'Count': Count,
    'Sum': Sum,
    'Avg': Avg,
    'Max': Max,
    'Min': Min,
    'StdDev': StdDev,
    'Variance': Variance,
    'Cast': Cast,
    'DecimalField': DecimalField,
    'FloatField': FloatField,
    'IntegerField': IntegerField,
    'CharField': CharField,
}


class DbExpression(Expression):
    function_set = {
        **Expression.function_set,
        **DB_FUNC,
    }


def resolve_expression(expression, variables=None):
    return DbExpression(variables).resolve(expression)
