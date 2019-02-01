from rest_framework import viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.export.fields import get_app_field_schema
from api_basebone.export.admin import get_app_admin_config


class ConfigViewSet(viewsets.GenericViewSet):
    """读取配置接口"""

    @action(detail=False, url_path='schema')
    def get_schema(self, request, *args, **kwargs):
        """获取 schema 配置"""
        data = get_app_field_schema()
        return success_response(data)

    @action(detail=False, url_path='admin')
    def get_admin(self, request, *args, **kwargs):
        """获取 admin 配置"""
        data = get_app_admin_config()
        return success_response(data)

    @action(detail=False, url_path='all')
    def get_all(self, request, *args, **kargs):
        """获取所有的客户端配置，包括schema, admin
        """
        data = {
            'schemas': get_app_field_schema(),
            'admins': get_app_admin_config()
        }
        return success_response(data)
