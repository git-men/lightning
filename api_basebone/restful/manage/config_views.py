from rest_framework import viewsets
from rest_framework.decorators import action

from api_basebone.drf.permissions import IsAdminUser
from api_basebone.drf.response import success_response
from api_basebone.export.admin import get_json_field_admin_config, ExportService
from api_basebone.export.fields import get_app_field_schema, get_app_json_field_schema
from api_basebone.export.setting import get_settins, get_setting_config
from api_basebone.utils.meta import load_custom_admin_module
from bsm_config.models import Admin
from bsm_config.signals import update_action_permission, create_action_permission

export_service = ExportService()


class ConfigViewSet(viewsets.GenericViewSet):
    """读取配置接口"""

    def _load_bsm_admin_module(self):
        """加载 bsm admin 模块"""
        load_custom_admin_module()

    @action(detail=False, url_path='schema', permission_classes = (IsAdminUser,))
    def get_schema(self, request, *args, **kwargs):
        """获取 schema 配置"""
        self._load_bsm_admin_module()
        data = get_app_field_schema()
        return success_response(data)

    @action(detail=False, url_path='admin', permission_classes = (IsAdminUser,))
    def get_admin(self, request, *args, **kwargs):
        self._load_bsm_admin_module()
        """获取 admin 配置"""
        data = export_service.get_app_admin_config(request)
        return success_response(data)

    def get_serializer(self):
        # 去掉会导致无法生成swagger文档，详见 rest_framework.schemas.inspectors.AutoSchema.get_serializer_fields
        return None

    @action(detail=False, methods=['put'], url_path='admin/(?P<model_name>[^/.]+)', permission_classes = (IsAdminUser,))
    def admin(self, request, model_name):
        admin, created = Admin.objects.get_or_create(model=model_name)
        old_config = admin.config
        admin.config = dict(request.data)
        if created:
            create_action_permission(*admin.model.split('__'), admin.config)
        else:
            update_action_permission(*admin.model.split('__'), admin.config, old_config)
        admin.save()
        return success_response()

    @action(detail=False, url_path='all', permission_classes = (IsAdminUser,))
    def get_all(self, request, *args, **kargs):
        """获取所有的客户端配置，包括schema, admin
        """
        self._load_bsm_admin_module()
        data = {
            'schemas': get_app_field_schema(),
            'admins': export_service.get_app_admin_config(request),
        }
        json_object_schemas, json_array_item_schemas = get_app_json_field_schema()
        json_admin_configs = get_json_field_admin_config(json_object_schemas,json_array_item_schemas)
        data['schemas'].update(json_object_schemas)
        data['schemas'].update(json_array_item_schemas)
        data['admins'].update(json_admin_configs)
        return success_response(data)

    @action(detail=False, url_path='settings')
    def get_web_settins(self, request, *args, **kargs):
        settings = get_settins()
        return success_response(settings)

    @action(detail=False, url_path='setting_config', permission_classes=(IsAdminUser,))
    def get_setting_config(self, request, *args, **kargs):
        settings = get_setting_config()
        return success_response(settings)

    @action(detail=False, url_path='manage/menu', permission_classes=(IsAdminUser,))
    def get_manage_menu(self, request, *args, **kwargs):
        """获取管理端的菜单配置"""
        menutype = request.query_params.get('menutype', 'database')
        return success_response(export_service.get_menu_data(self.request, menutype=menutype))
