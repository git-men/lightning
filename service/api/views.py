import importlib

from django.apps import apps
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action

from utils import exceptions
from utils.api_response import success_response

from .operators import build_filter_conditions
from .serializers import create_serializer_class, multiple_create_serializer_class


# 常量声明

# 客户端传入过滤条件的关键字
FILTER_CONDITIONS = 'filters'
# 客户端传入展示字段的关键字
DISPLAY_FIELDS = 'display_fields'
# 展开字段的传入
EXPAND_FIELDS = 'expand_fields'


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
        """
        截断，校验对应的 app 和 model 是否合法以及赋予当前对象对应的属性值
        """
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

        self.get_expand_fields()
        return result

    def get_expand_fields(self):
        """获取扩展字段并作为属性值赋予"""
        if self.action in ['list', 'retrieve']:
            fields = self.request.query_params.get(EXPAND_FIELDS)
            self.expand_fields = fields.split(',') if fields else None
        else:
            self.expand_fields = self.request.data.get(EXPAND_FIELDS)

    def get_queryset(self):
        """动态的计算结果集

        这里做好是否关联查询
        """

        expand_fields = self.expand_fields
        if not expand_fields:
            return self.model.objects.all()

        field_list = [item.replace('.', '__') for item in expand_fields]
        return self.model.objects.all().prefetch_related(*field_list)

    def get_serializer_class(self, expand_fields=None):
        """动态的获取序列化类"""
        if not self.expand_fields:
            return create_serializer_class(self.model)
        return multiple_create_serializer_class(self.model, self.expand_fields)

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
