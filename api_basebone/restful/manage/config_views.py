from bsm_config.models import Admin
from bsm_config.signals import update_action_permission, create_action_permission
from django.apps import apps
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action

from api_basebone.drf.permissions import IsAdminUser
from api_basebone.drf.response import success_response
from api_basebone.export.admin import get_app_admin_config, get_json_field_admin_config, ExportService
from api_basebone.export.fields import get_app_field_schema, get_app_json_field_schema
from api_basebone.export.menu import get_menu_from_database, get_menu_from_settings
from api_basebone.export.setting import get_settins, get_setting_config
from api_basebone.utils import module
from api_basebone.utils.meta import load_custom_admin_module, get_export_apps

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

    @action(detail=False, url_path='setting_config')
    def get_setting_config(self, request, *args, **kargs):
        settings = get_setting_config()
        return success_response(settings)
    
    def _get_menu_from_database(self):
        menus_data = get_menu_from_database(self.request.user)
        return success_response(menus_data)

    def _get_menu_from_custom(self):
        """从自定义的菜单配置中获取菜单"""
        menu_module = module.get_bsm_global_module(module.BSM_GLOBAL_MODULE_MENU)
        result = getattr(menu_module, module.BSM_GLOBAL_MODULE_MENU_MANAGE, None)

        by_role = getattr(settings, 'BSM_MANAGE_MENU_BY_ROLE', False)
        if not by_role:
            return success_response(result['default'])
        else:
            groups = {
                item.name
                for item in self.request.user.groups.all()
            }
            if not groups:
                return success_response([])

            for item in groups:
                if item in result:
                    return success_response(result[item])
            
        return success_response([])

    def _get_menu_from_autobuild(self):
        """根据模型自定义菜单"""
        export_apps = get_export_apps()
        if not export_apps:
            return success_response([])
        try:
            result, id_index = [], 0
            for app_name in export_apps:
                application = apps.get_app_config(app_name)
                for model_item in application.get_models():
                    id_index += 1
                    result.append(
                        {
                            "id": id_index,
                            "name": model_item._meta.verbose_name,
                            "icon": None,
                            "parent": None,
                            "page": "list",
                            "permission": None,
                            "model": f"{app_name}__{model_item._meta.model_name}",
                            "sequence": 0,
                            "menu": []
                        }
                    )
            return success_response(result)
        except Exception:
            return success_response([])

    @action(detail=False, url_path='manage/menu', permission_classes=(IsAdminUser,))
    def get_manage_menu(self, request, *args, **kwargs):
        """获取管理端的菜单配置"""
        if hasattr(settings, 'ADMIN_MENUS'):
            return success_response(get_menu_from_settings(self.request.user))

        menutype = request.query_params.get('menutype', 'database')
        if menutype == 'database':
            return self._get_menu_from_database()
        if menutype == 'custom':
            return self._get_menu_from_custom()
        if menutype == 'autobuild':
            return self._get_menu_from_autobuild()


