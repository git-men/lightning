import importlib

from django.apps import apps
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action

from utils import exceptions
from utils.api_response import success_response

from .const import (
    DISPLAY_FIELDS,
    EXPAND_FIELDS,
    FILTER_CONDITIONS,
)
from .forms import create_form_class
from .operators import build_filter_conditions
from .serializers import create_serializer_class, multiple_create_serializer_class


class FormMixin(object):
    """表单处理"""

    def get_create_form(self):
        """获取创建数据的验证表单"""
        return create_form_class(self.model)

    def get_update_form(self):
        """获取更新数据的验证表单"""
        return create_form_class(self.model)

    def get_validate_form(self, action):
        """获取验证表单"""
        return getattr(self, 'get_{}_form'.format(action))()


class CommonManageViewSet(viewsets.ModelViewSet, FormMixin):
    """通用的管理接口视图"""

    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

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
        """获取扩展字段并作为属性值赋予

        注意使用扩展字段 get 方法和 post 方法的区别

        get 方法使用 query string，这里需要解析
        post 方法直接放到 body 中
        """
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
        """动态的获取序列化类

        - 如果没有嵌套字段，则动态创建最简单的序列化类
        - 如果有嵌套字段，则动态创建引用字段的嵌套序列化类
        """
        if not self.expand_fields:
            return create_serializer_class(self.model)
        return multiple_create_serializer_class(self.model, self.expand_fields)

    def _get_filter_queryset(self, queryset):
        """
        此方法只用于 set 方法，用于检测客户端传入的过滤条件

        TODO: 详情页需要考虑筛选条件，这里考量获取详情是否也使用 POST 方法

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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        这里校验表单和序列化类分开创建

        原因：序列化类有可能嵌套
        """
        serializer = self.get_validate_form(self.action)(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer)

        # 如果有联合查询，单个对象创建后并没有联合查询
        instance = self.get_queryset().filter(id=instance.id).first()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_validate_form(self.action)(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        instance = self.perform_update(serializer)
        serializer = self.get_serializer(instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return success_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response()

    @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):
        """获取列表数据"""
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
