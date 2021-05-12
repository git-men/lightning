import re
import json
import logging
import operator
from datetime import timedelta
from collections import namedtuple
from decimal import Decimal
from functools import reduce
from django.utils import timezone
from django.db.models import *
from django.db.models.functions import Concat, Cast, Coalesce

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
    'first_day_of_month': lambda: timezone.now().date().replace(day=1),
    'days_after': lambda days: timezone.now().date() + timedelta(days=days),
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
    def split_expression(expression, sep=','):
        expression = expression.strip()
        quote = False
        surround = 0
        buffer = ''
        escape = False
        for char in expression:
            if escape and quote:
                escape = False
            else:
                if char == sep:
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
        args = tuple(self.resolve(buffer) for buffer in arguments)
        log.debug(f'returning calling Fun: {function_name} with args: {args}')
        return self.function_set[function_name](*args)

    def resolve(self, expression):
        expression = expression.strip()

        try:
            return json.loads(expression)
        except json.JSONDecodeError:
            pass
        log.debug(f'resolving expression: {expression}')
        matched = re.match(r'^(\w+)\((.*)\)$', expression, flags=re.DOTALL)
        if matched:
            func, arg_str = matched.groups()
            return self.execute_function(func, self.split_expression(arg_str))
        log.error(f'error when resolving expression: {expression}')
        raise NotImplementedError()


class Expression(BaseExpression):
    def __init__(self, variable_root=None):
        self.variable_root = variable_root

    @property
    def function_set(self):
        super_set = super().function_set
        return {
            **super_set,
            '__variable_root__': lambda: self.variable_root,
        }

    def resolve(self, expression):
        try:
            return super().resolve(expression)
        except NotImplementedError:
            if '.' in expression:
                # 点操作符，getattr的语法糖
                return self.resolve(reduce(lambda exp, seg: f'__getattr__({exp}, "{seg}")', expression.split('.')))
            return self.resolve('__getattr__(__variable_root__(), "{}")'.format(expression))


def aggregation_align(aggregation):
    return lambda expression, q=None: aggregation(expression, filter=q)


DB_FUNC = {
    'Condition': lambda field, lookup, value: Q(**{f'{field}__{lookup}': value}),
    'ConditionOr': reduce_wrap(operator.or_),
    'ConditionAnd': reduce_wrap(operator.and_),
    'F': F,
    'Q': Q,
    'Concat': Concat,
    'Value': Value,
    'Count': Count,
    'Sum': aggregation_align(Sum),
    'Avg': aggregation_align(Avg),
    'Max': aggregation_align(Max),
    'Min': aggregation_align(Min),
    'StdDev': StdDev,
    'Variance': Variance,
    'Cast': Cast,
    'Coalesce': Coalesce,
    'When': When,
    'Case': lambda *cases: Case(*cases) if isinstance(cases[-1], When) else Case(*cases[:-1], default=cases[-1]),
    'DecimalField': lambda max_digits, decimal_places: DecimalField(max_digits=max_digits, decimal_places=decimal_places),
    'FloatField': FloatField,
    'IntegerField': IntegerField,
    'CharField': CharField,
    'DurationField': DurationField,
    'ExpressionWrapper': ExpressionWrapper,
}


class DbExpression(Expression):
    @property
    def function_set(self):
        super_set = super().function_set
        return {
            **super_set,
            **DB_FUNC,
        }


def resolve_expression(expression, variables=None):
    return DbExpression(variables).resolve(expression)


class SubqueryAggregate(namedtuple('SubqueryAggregate', ['aggregation', 'model'])):
    def __call__(self, field_path, q=None):
        aggregation = self.aggregation
        if '__' not in field_path:
            return aggregation(field_path, q)
        model = self.model
        reverse_path = []
        path_parts = field_path.split('__')
        for part in path_parts[:-1]:
            try:
                next_field = model._meta.get_field(part).remote_field
            except:
                return aggregation(field_path, q)
            model = next_field.model
            reverse_path.insert(0, next_field.name)

        outer_ref_name = self.model._meta.get_field(path_parts[0]).target_field.name
        query_path = '__'.join(reverse_path + [outer_ref_name])
        from api_basebone.utils import queryset as queryset_util
        return Subquery(queryset_util.annotate(model.objects.all()).filter(q or Q(), **{query_path: OuterRef(outer_ref_name)}).values(query_path).annotate(__result__=aggregation(path_parts[-1])).values('__result__'))


class FieldExpression(DbExpression):
    def __init__(self, model, variable_root=None):
        self.model = model
        super().__init__(variable_root)

    def f(self, field_path):
        if '__' not in field_path:
            return F(field_path)
        model = self.model
        reverse_path = []
        path_parts = field_path.split('__')
        for part in path_parts[:-1]:
            try:
                next_field = model._meta.get_field(part).remote_field
            except:
                return F(field_path)
            model = next_field.model
            reverse_path.insert(0, next_field.name)

        try:
            model._meta.get_field(path_parts[-1])
        except FieldDoesNotExist:
            query_path = '__'.join(reverse_path)
            from api_basebone.utils import queryset as queryset_util
            return Subquery(queryset_util.annotate(model.objects.all()).filter(**{query_path: OuterRef(self.model._meta.get_field(path_parts[0]).target_field.name)}).values(path_parts[-1])[:1])

        return F(field_path)

    @property
    def function_set(self):
        super_set = super().function_set
        return {
            **super_set,
            'Sum': SubqueryAggregate(Sum, model=self.model),
            'Avg': SubqueryAggregate(Avg, model=self.model),
            'Max': SubqueryAggregate(Max, model=self.model),
            'Min': SubqueryAggregate(Min, model=self.model),
            'F': self.f,
        }
