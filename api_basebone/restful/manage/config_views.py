from rest_framework import viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.export.admin import get_app_admin_config
from api_basebone.export.fields import get_app_field_schema
from api_basebone.utils import module
from api_basebone.utils.meta import load_custom_admin_module


class ConfigViewSet(viewsets.GenericViewSet):
    """读取配置接口"""

    def _load_bsm_admin_module(self):
        """加载 bsm admin 模块"""
        load_custom_admin_module()

    @action(detail=False, url_path='schema')
    def get_schema(self, request, *args, **kwargs):
        """获取 schema 配置"""
        self._load_bsm_admin_module()
        data = get_app_field_schema()
        return success_response(data)

    @action(detail=False, url_path='admin')
    def get_admin(self, request, *args, **kwargs):
        self._load_bsm_admin_module()
        """获取 admin 配置"""
        data = get_app_admin_config()
        return success_response(data)

    @action(detail=False, url_path='all')
    def get_all(self, request, *args, **kargs):
        """获取所有的客户端配置，包括schema, admin
        """
        self._load_bsm_admin_module()
        data = {'schemas': get_app_field_schema(), 'admins': get_app_admin_config()}
        return success_response(data)

    @action(detail=False, url_path='manage/menu')
    def get_manage_menu(self, request, *args, **kwargs):
        """获取管理端的菜单配置"""
        menu_module = module.get_bsm_global_module(module.BSM_GLOBAL_MODULE_MENU)
        result = getattr(menu_module, module.BSM_GLOBAL_MODULE_MENU_MANAGE, None)
        return success_response(result)
