from functools import partial
import logging

import pytz
from django.db.models import Sum, Count, Value, F, Avg, Max, Min
from django.db.models.fields.related import (
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    ForeignKey,
    OneToOneField,
    OneToOneRel,
)
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncHour

from rest_framework.decorators import action

from api_basebone.core import admin, exceptions
from api_basebone.drf.response import success_response
from api_basebone.restful import const
from api_basebone.restful.serializers import get_model_exclude_fields
from api_basebone.utils.meta import get_all_relation_fields
from api_basebone.utils.meta import get_bsm_model_admin
from api_basebone.models import AdminLog
from api_basebone.settings import settings as basebone_settings
from api_basebone.services.expresstion import resolve_expression
from .forms import get_form_class
from api_basebone.utils.operators import build_filter_conditions2

log = logging.getLogger(__name__)


class CheckValidateMixin:
    """检测校验"""

    def basebone_check_distinct_queryset(self, fields):
        """检测是否需要

        检测是否需要对结果集去重，去重需要单独做好检测
        因为去重在统计业务中，如果去重，对于关联的查询，会做子查询，导致
        结果不符合预期

        这里对于关系字段都需要做去重操作

        - 一对多
        - 多对一
        - 多对多
        """
        # 如果动作是创建或者跟单条数据相关的，不在进行去重操作
        if self.action in [
            'create',
            'retrieve',
            'destroy',
            'custom_patch',
            'update',
            'partial_update',
        ]:
            return

        if not fields:
            return

        # 获取非一对一的关系字段
        relation_fields = [
            item.name
            for item in get_all_relation_fields(self.model)
            if not item.one_to_one
        ]

        if not isinstance(fields, list):
            fields = [fields]

        separator = '__'

        for item in fields:
            if not isinstance(item, str):
                continue
            field = item.split(separator)[0]
            if field in relation_fields:
                self.basebone_distinct_queryset = True
                break


class StatisticsMixin:
    """获取统计数据"""

    def basebone_get_statistics_config(self):
        """
        FIXME: 获取统计配置，暂时只支持管理端，客户端待完成
        """
        if self.end_slug == const.MANAGE_END_SLUG:
            # 如果是管理端的配置，直接使用 admin 中的配置
            admin_class = self.get_bsm_model_admin()
            if admin_class:
                config = getattr(admin_class, admin.BSM_STATISTICS, None)
                if not config:
                    raise exceptions.BusinessException(
                        error_code=exceptions.BSM_NOT_STATISTICS_CONFIG
                    )
                return config
            raise exceptions.BusinessException(
                error_code=exceptions.BSM_CAN_NOT_FIND_ADMIN
            )

    @action(methods=['post'], detail=False, url_path='statistics')
    def statistics(self, request, *args, **kwargs):
        """计算统计数据

        请求的数据结构如下：

        {
            key: {
                method: 'count'
                field: 'xxxx',
                verbose_name: '可读名称',
            },
            ...
        }
        """
        log.debug(f'statistics action: {self.action}')
        configs = request.data.get('fields', None)
        if not configs:
            configs = self.basebone_get_statistics_config()
        if not configs:
            return success_response({})

        queryset = self.get_queryset()

        method_map = {'sum': Sum, 'count': Count}

        aggregates, relation_aggregates = {}, {}

        relation_fields = [
            item.name for item in get_all_relation_fields(self.model)]

        for key, value in configs.items():
            if not isinstance(value, dict):
                continue

            method = value.get('method')

            if method not in method_map:
                continue

            field = value.get('field') if value.get('field') else key
            aggregate_param = method_map[value['method']](field)

            if method == 'count':
                aggregate_param = method_map[value['method']](
                    field, distinct=True)

            condition = Coalesce(aggregate_param, Value(0))

            split_field = field.split('__')[0]
            if split_field in relation_fields:
                relation_aggregates[key] = condition
            else:
                aggregates[key] = condition

        if not aggregates and not relation_aggregates:
            return success_response({})

        result = queryset.aggregate(**aggregates)
        origin_queryset = self.basebone_origin_queryset or queryset
        origin_queryset.query.annotations.clear()
        relation_result = origin_queryset.aggregate(
            **relation_aggregates)

        result.update(relation_result)
        return success_response(result)


class GroupStatisticsMixin:
    """获取统计数据"""

    def get_group(self):
        request = self.request
        if 'group' in request.data:
            group = request.data.get('group')
        else:
            # 正佳的项目用了group_method和group_by的方式
            group_method = request.data.get('group_method', None)
            group_by = request.data.get('group_by')
            group = {'group': {'method': group_method, 'field': group_by}}

        return self.get_group_data(group)

    def get_group_data(self, group):
        group_functions = {
            'TruncDay': partial(TruncDay, tzinfo=pytz.UTC),
            'TruncMonth': partial(TruncMonth, tzinfo=pytz.UTC),
            'TruncHour': partial(TruncHour, tzinfo=pytz.UTC),
            None: F,
        }

        # TODO 解决重名的方法，例如供应商名称传过来的是'agency.name'，那么SQL应该同时group by agency_id 和 agency__name，而不单单是agency__name
        # 支持一下使用计算字段作为
        data = {}
        for k, v in group.items():
            if v.get('expression', None):
                expression = resolve_expression(v['expression'])
                log.debug(
                    f'expression before: {v["expression"]} after resolve: {expression}'
                )
                data[k] = expression
            else:
                data[k] = group_functions[v.get('method', None)](
                    v['field'].replace('.', '__')
                )

        return data

    def group_statistics_data(self, fields, group_kwargs, *args, **kwargs):
        """
        分组统计
        """
        methods = {
            'sum': Sum,
            'Sum': Sum,
            'count': Count,
            'Count': Count,
            'Avg': Avg,
            'Max': Max,
            'Min': Min,
            None: F,
        }
        log.debug(
            f'static parameters, fields: {fields}, groups: {group_kwargs}')
        queryset = (
            self.get_queryset().annotate(**group_kwargs).values(*group_kwargs.keys())
        )
        result = queryset.annotate(
            **{
                key: methods[value.get('method', None)](
                    value['field'].replace('.', '__'),
                    **{'distinct': value['distinct']} if 'distinct' in value else {}
                )
                for key, value in fields.items()
                # 排除exclude_fields
                if not value.get('expression', None) and value.get('field', None) not in get_model_exclude_fields(self.model, None)
            },
            **{
                key: resolve_expression(value['expression'])
                for key, value in fields.items()
                if value.get('expression', None)
            }
        ).order_by(*group_kwargs.keys())
        # 支持排序
        sort_keys = kwargs.get('sort_keys', [])
        top_max = kwargs.get('top_max', None)
        SORT_ASCE = 'asce'
        SORT_DESC = 'desc'
        all_keys = list(fields.keys()) + list(group_kwargs.keys())
        if sort_keys:
            import re

            keys_set = set([re.sub(r'-', "", key) for key in sort_keys])
            if not (keys_set & set(all_keys) == keys_set):
                pass
            result = result.order_by(*sort_keys)
        # 支持对聚合后的数据进行filter
        filters = kwargs.get('filters', [])
        if filters:
            con = build_filter_conditions2(filters)
            result = result.filter(con)
        # 筛选前N条
        if top_max:
            result = result[:top_max]
        # TODO 考虑使用DRF来序列化查询结果

        return result

    @action(methods=['post'], detail=False, url_path='group_statistics')
    def group_statistics(self, request, *args, **kwargs):
        fields = request.data.get('fields')
        filters = request.data.pop('filters', [])
        group_kwargs = self.get_group()

        data = self.group_statistics_data(fields, group_kwargs, filters=filters)
        return success_response(data)

    @action(methods=['post'], detail=False, url_path='get_chart')
    def get_chart(self, request, *args, **kwargs):
        log.debug(f'get_chart action: {self.action}')
        from chart.models import Chart
        from django.core.cache import cache

        id = request.data['id']
        chart = cache.get(f'chart_config:{id}', None)
        log.debug(f'chart get from cache: {chart}')
        if chart is None:
            chart = Chart.objects.prefetch_related(
                'metrics', 'dimensions', 'chart_filters'
            ).get(id=id)
            cache.set(f'chart_config:{id}', chart, 600)
            log.debug('cached Chart')

        group = {}
        fields = {}
        for dimension in chart.dimensions.all():
            field = {
                'field': dimension.field,
                'displayName': dimension.display_name,
                'expression': dimension.expression,
            }
            if dimension.method:
                field['method'] = dimension.method
            if dimension.name == 'groupby':
                group[dimension.name] = field
            if dimension.name == 'legend':
                group[dimension.name] = field

        for metric in chart.metrics.all():
            field = {
                'field': metric.field,
                'method': metric.method,
                'expression': metric.expression,
                'displayName': metric.display_name,
                'format': metric.format,
            }
            fields[metric.name] = field
        group_kwargs = self.get_group_data(group)
        filters = [
            {'field': ft.field, 'operator': ft.operator, 'value': ft.value, 'children': ft.children}
            for ft in chart.chart_filters.all().prefetch_related('children')
        ]
        data = self.group_statistics_data(
            fields,
            group_kwargs,
            sort_keys=chart.sort_keys,
            top_max=chart.top_max,
            filters=filters,
        )
        return success_response(data)

class FormMixin(object):
    """表单处理集合"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return get_form_class(self.model, 'create', end=self.end_slug, request=self.request)

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return get_form_class(self.model, 'update', end=self.end_slug, request=self.request)

    def get_partial_update_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug, request=self.request)

    def get_custom_patch_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug, request=self.request)

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()

    def get_bsm_model_admin(self):
        """获取 BSM Admin 模块"""
        return get_bsm_model_admin(self.model)
