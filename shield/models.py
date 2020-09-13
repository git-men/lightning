from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group

from api_basebone.utils.operators import OPERATOR_MAP


class Rule(models.Model):
    COMBINATOR_AND = '&'
    COMBINATOR_OR = '|'

    model = models.ForeignKey(settings.SHIELD_MODEL, on_delete=models.CASCADE, verbose_name='关联模型')\
        if hasattr(settings, 'SHIELD_MODEL') else models.CharField('关联模型', max_length=191)
    groups = models.ManyToManyField(Group, verbose_name='关联用户组', help_text='不选会应用于全部', blank=True)
    combinator = models.CharField('组合方式', choices=((COMBINATOR_AND, '与'), (COMBINATOR_OR, '或')), max_length=1, default=COMBINATOR_AND)

    def get_rule(self):
        conditions = [c.to_dict() for c in self.condition_set.all()]
        return {
            'conditions': conditions if self.combinator == self.COMBINATOR_AND else [{'operator': 'OR', 'children': conditions}],
            'groups': {r.name for r in self.groups.all()},
        }

    class Meta:
        verbose_name = '规则'
        verbose_name_plural = verbose_name


class Condition(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, verbose_name='所属规则')
    field = models.CharField('字段', max_length=100)
    operator = models.CharField('操作符', choices=[(o, o) for o in OPERATOR_MAP.keys()], max_length=20, default='=')
    variable = models.CharField('变量', choices=[['user', '用户']], max_length=50, default='user')

    def to_dict(self):
        return {'field': self.field.replace('.', '__'), 'operator': self.operator, 'expression': self.variable}

    class Meta:
        verbose_name = '过滤条件'
        verbose_name_plural = verbose_name
