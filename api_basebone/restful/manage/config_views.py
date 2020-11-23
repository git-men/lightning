from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from api_basebone.restful.serializers import (
    create_serializer_class
)

from api_basebone.restful.const import MANAGE_END_SLUG
from api_basebone.drf.response import success_response
from api_basebone.export.admin import get_app_admin_config, get_json_field_admin_config
from api_basebone.export.fields import get_app_field_schema, get_app_json_field_schema
from api_basebone.export.setting import get_settins, get_setting_config
from api_basebone.utils import module
from api_basebone.utils.meta import load_custom_admin_module, get_export_apps
from bsm_config.models import Menu, Admin
from api_basebone.utils import queryset as queryset_utils
from api_basebone.drf.permissions import IsAdminUser


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
        data = get_app_admin_config()
        return success_response(data)

    def get_serializer(self):
        # 去掉会导致无法生成swagger文档，详见 rest_framework.schemas.inspectors.AutoSchema.get_serializer_fields
        return None

    @action(detail=False, methods=['put'], url_path='admin/(?P<model_name>[^/.]+)', permission_classes = (IsAdminUser,))
    def admin(self, request, model_name):
        model, created = Admin.objects.get_or_create(model=model_name)
        model.config = dict(request.data)
        model.save()
        return success_response()

    @action(detail=False, url_path='all', permission_classes = (IsAdminUser,))
    def get_all(self, request, *args, **kargs):
        """获取所有的客户端配置，包括schema, admin
        """
        self._load_bsm_admin_module()
        data = {
            'schemas': get_app_field_schema(),
            'admins': get_app_admin_config()
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
        """从数据库中获取菜单"""
        user = self.request.user
        # permissions = self.request.user.get_all_permissions()
        # permission_filter = (Q(permission=None) | Q(permission='') | Q(permission__in=permissions))
        menus =  Menu.objects.prefetch_related('parent').order_by('sequence','id') if user.is_superuser else \
              Menu.objects.filter(Q(groups__in=self.request.user.groups.all()) | Q(groups__isnull=True)).prefetch_related('parent').order_by('sequence','id')
        fields =  { field.name for field in Menu._meta.fields } - {'id', 'parent',  'permission', 'name'}
        menus_map = { menu.id: dict({ field: getattr(menu, field) for field in fields }, **{ 'name': menu.display_name, 'parent_id': menu.parent_id, 'children': [] }) for menu in menus }
        for _, menu in menus_map.items():
            parent_id = menu['parent_id']
            if parent_id and parent_id in menus_map:
                menus_map[parent_id]['children'].append(menu)
        menus_data = [ m for _, m in menus_map.items() if not m.get('parent_id')] 
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
            group_names = self.request.user.groups.values_list('name', flat=True)
            group_names = set(group_names)

            def map_menus(menus):
                return [
                    {**m, 'children': map_menus(m.get('children', []))}
                    for m in menus if 'groups' not in m or self.request.user.is_superuser or set(m['groups']) & group_names
                ]
            return success_response(map_menus(settings.ADMIN_MENUS))

        menutype = request.query_params.get('menutype', 'database')
        if menutype == 'database':
            return self._get_menu_from_database()
        if menutype == 'custom':
            return self._get_menu_from_custom()
        if menutype == 'autobuild':
            return self._get_menu_from_autobuild()


