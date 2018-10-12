import importlib
from django.apps import apps
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action

from utils.api_response import success_response
from utils import exceptions


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
        """获取序列化类

        如果是 Django 模型，则需要找到匹配的序列化类
        如果是字符模型，则返回 RecordSerializer
        """

        module_path = f'{self.app_label}.restful'
        serializer_name = f'{self.model_slug}Serializer'
        module = importlib.import_module(module_path)
        return getattr(module, serializer_name)

    def list(self, request, **kwargs):
        return success_response({'age': 23, 'name': 'kycool'})

    @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):

        # serializer_class = self.get_serializer_class()
        # queryset = self.get_queryset()
        # serializer = serializer_class(queryset, many=True)
        # return success_response(serializer.data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return success_response(response.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
