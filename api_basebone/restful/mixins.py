from functools import partial

from django.db.models import Sum, Count, Value, F
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncHour

from rest_framework.decorators import action

from api_basebone.core import admin, exceptions
from api_basebone.drf.response import success_response
from api_basebone.restful import const
from api_basebone.utils.meta import get_all_relation_fields


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
        configs = self.basebone_get_statistics_config()
        if not configs:
            return success_response({})

        queryset = self.get_queryset()

        method_map = {
            'sum': Sum,
            'count': Count,
        }

        aggregates, relation_aggregates = {}, {}

        relation_fields = [
            item.name for item in get_all_relation_fields(self.model)
        ]

        for key, value in configs.items():
            if not isinstance(value, dict):
                continue

            method = value.get('method')

            if method not in method_map:
                continue

            field = value.get('field') if value.get('field') else key
            aggregate_param = method_map[value['method']](field)

            if method == 'count':
                aggregate_param = method_map[value['method']](field, distinct=True)

            condition = Coalesce(aggregate_param, Value(0))

            split_field = field.split('__')[0]
            if split_field in relation_fields:
                relation_aggregates[key] = condition
            else:
                aggregates[key] = condition

        if not aggregates and not relation_aggregates:
            return success_response({})

        result = queryset.aggregate(**aggregates)
        relation_result = self.basebone_origin_queryset.aggregate(**relation_aggregates)

        result.update(relation_result)
        return success_response(result)


class GroupStatisticsMixin:
    """获取统计数据"""
    @action(methods=['post'], detail=False, url_path='group_statistics')
    def group_statistics(self, request, *args, **kwargs):
        """
        分组统计
        """
        group_functions = {
            'TruncDay': TruncDay,
            'TruncMonth': TruncMonth,
            'TruncHour': TruncHour,
            None: F,
        }
        methods = {
            'sum': Sum,
            'count': partial(Count, distinct=True),
        }
        group_method = request.data.get('group_method', None)
        group_by = request.data.get('group_by')
        fields = request.data.get('fields')
        result = self.get_queryset().annotate(group=group_functions[group_method](group_by)).values('group').annotate(
            **{key: methods[value['method']](value['field']) for key, value in fields.items()}).order_by('group')

        return success_response(result)
