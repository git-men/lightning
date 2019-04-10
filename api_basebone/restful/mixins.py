from django.db.models import Count, Sum
from rest_framework.decorators import action
from api_basebone.core import admin, exceptions
from api_basebone.drf.response import success_response
from api_basebone.restful import const


class StatisticsMixin:
    """获取统计数据"""

    def _get_statistics_config(self):
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
        configs = self._get_statistics_config()
        if not configs:
            return success_response({})

        queryset = self.filter_queryset(self.get_queryset())

        method_map = {
            'sum': Sum,
            'count': Count,
        }

        aggregates = {}
        for key, value in configs.items():
            if not isinstance(value, dict):
                continue

            method = value.get('method')

            if method not in method_map:
                continue

            field = value.get('field') if value.get('field') else key
            aggregates[key] = method_map[value['method']](field)

        if not aggregates:
            return success_response({})

        result = queryset.aggregate(**aggregates)
        return success_response(result)
