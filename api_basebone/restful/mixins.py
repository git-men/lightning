from functools import partial

import pytz
from django.db.models import Sum, Count, Value, F, Avg, Max, Min
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
from .forms import get_form_class


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
        configs = request.data.get('fields', None)
        if not configs:
            configs = self.basebone_get_statistics_config()
        if not configs:
            return success_response({})

        queryset = self.get_queryset()

        method_map = {'sum': Sum, 'count': Count}

        aggregates, relation_aggregates = {}, {}

        relation_fields = [item.name for item in get_all_relation_fields(self.model)]

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
        self.basebone_origin_queryset.query.annotations.clear()
        relation_result = self.basebone_origin_queryset.aggregate(**relation_aggregates)

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

        group_functions = {
            'TruncDay': partial(TruncDay, tzinfo=pytz.UTC),
            'TruncMonth': partial(TruncMonth, tzinfo=pytz.UTC),
            'TruncHour': partial(TruncHour, tzinfo=pytz.UTC),
            None: F,
        }

        # TODO 解决重名的方法，例如供应商名称传过来的是'agency.name'，那么SQL应该同时group by agency_id 和 agency__name，而不单单是agency__name
        return {k: group_functions[v.get('method', None)](v['field'].replace('.', '__')) for k, v in group.items()}

    def get_queryset_by_filter_conditions(self, queryset):
        if self.action == 'group_statistics':
            queryset = queryset.annotate(**self.get_group())
        return super().get_queryset_by_filter_conditions(queryset)

    @action(methods=['post'], detail=False, url_path='group_statistics')
    def group_statistics(self, request, *args, **kwargs):
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

        fields = request.data.get('fields')
        group_kwargs = self.get_group()
        result = (
            self.get_queryset()
            .values(*group_kwargs.keys())
            .annotate(
                **{key: methods[value.get('method', None)](value['field'].replace('.', '__'), distinct=value.get('distinct', False)) for key, value in fields.items()
                   # 排除exclude_fields
                   if value['field'] not in get_model_exclude_fields(self.model, None)}
            )
            .order_by(*group_kwargs.keys())
        )
        # TODO 考虑使用DRF来序列化查询结果
        return success_response(result)


class ActionLogMixin:
    """动作记录"""

    def initial(self, request, *args, **kwargs):
        result = super().initial(request, *args, **kwargs)

        if self.app_label == 'api_basebone' and self.model_slug == 'adminlog':
            return result

        if basebone_settings.MANAGE_USE_ACTION_LOG:
            AdminLog.objects.create(
                user=self.request.user,
                action=self.action,
                app_label=self.app_label,
                model_slug=self.model_slug,
                object_id=self.kwargs.get('pk', ''),
                params=request.data,
            )
        return result


class FormMixin(object):
    """表单处理集合"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return get_form_class(self.model, 'create', end=self.end_slug)

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_partial_update_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_custom_patch_form(self):
        return get_form_class(self.model, 'update', end=self.end_slug)

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()

    def get_bsm_model_admin(self):
        """获取 BSM Admin 模块"""
        return get_bsm_model_admin(self.model)

