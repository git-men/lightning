import importlib

from django.apps import apps
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action

from utils.api_response import success_response
from utils import exceptions

from .operators import build_filter_conditions


# 常量声明

# 客户端传入过滤条件的关键字
FILTER_CONDITIONS = 'filters'
# 客户端传入展示字段的关键字
DISPLAY_FIELDS = 'display_fields'


class FormMixin(object):
    """表单处理"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        pass

    def get_update_form(self):
        """获取更新数据的验证表单"""
        pass

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()


class CommonManageViewSet(viewsets.ModelViewSet, FormMixin):
    """通用的管理接口视图"""

    def perform_authentication(self, request):
        result = super().perform_authentication(request)
        self.app_label, self.model_slug = self.kwargs.get('app'), self.kwargs.get('model')

        if self.app_label not in settings.INSTALLED_APPS:
            raise exceptions.BusinessException(
                error_code=exceptions.APP_LABEL_IS_INVALID
            )

        if self.model_slug not in apps.all_models[self.app_label]:
            raise exceptions.BusinessException(
                error_code=exceptions.MODEL_SLUG_IS_INVALID
            )

        try:
            self.model = apps.get_model(f'{self.app_label}.{self.model_slug}')
        except Exception:
            raise exceptions.BusinessException(
                error_code=exceptions.CANT_NOT_GET_MODEL
            )
        return result

    def get_queryset(self, display_fields=None):
        """动态的计算结果集"""

        queryset = self.model.objects.all()
        return queryset

    def get_serializer_class(self):
        """动态的获取序列化类"""
        module_path = f'{self.app_label}.restful'
        serializer_name = f'{self.model_slug}Serializer'
        module = importlib.import_module(module_path)
        return getattr(module, serializer_name)

    def _get_filter_queryset(self, queryset):
        """
        此方法只用于 set 方法，用于检测客户端传入的过滤条件

        客户端传入的过滤条件的数据结构如下：

        [
            {
                field: xxxx,
                operator: xxxx,
                value: xxxx
            }
        ]
        """
        if not queryset:
            return queryset

        filter_conditions = self.request.data.get(FILTER_CONDITIONS)
        if filter_conditions:
            cons = build_filter_conditions(filter_conditions)
            if cons:
                return queryset.filter(cons)
            return queryset
        return queryset

    @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.exists():
            queryset = self._get_filter_queryset(queryset)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
