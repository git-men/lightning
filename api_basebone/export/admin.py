from django.apps import apps
from django.conf import settings
from django.db.models import Q

from api_basebone.core.admin import BSMAdmin
from api_basebone.core.admin import BSMAdminModule
from api_basebone.utils import meta, module
from api_basebone.utils.meta import get_export_apps
from bsm_config.models import Admin, Menu
from bsm_config.bsm.functions import get_field_permissions


class BSMAdminConfig:
    """BSM admin 输出"""

    def validate_filter(self, key, value):
        """校验过滤筛选器"""
        pass

    def validate_display(self, key, value):
        """校验展示字段"""
        pass

    def validate_form_fields(self, key, value):
        """校验表单字段"""
        pass

    def validate(self, key, value):
        """校验 BSM Admin 配置项"""
        pass

bsm_admin_config = BSMAdminConfig()


def get_app_admin_config(request=None):
    """获取应用管理端的配置"""
    export_apps, config = meta.get_export_apps(), {}
    if not export_apps:
        return config

    for admin in Admin.objects.all():
        config[admin.model] = admin.config
        config[admin.model]['_id'] = admin.id
        config[admin.model]['field_permissions'] = get_field_permissions(None, admin.model)

    # 动态加载 amdin 模块
    meta.load_custom_admin_module()

    for key, cls in BSMAdminModule.modules.items():
        if issubclass(cls, BSMAdmin):
            config[key] = cls(request).to_dict()
        else:
            config[key] = BSMAdmin.to_dict(cls)
    return config


class ExportService:
    @staticmethod
    def get_app_admin_config(request=None):
        return get_app_admin_config(request)

    @staticmethod
    def _get_menu_from_custom(user):
        """从自定义的菜单配置中获取菜单"""
        menu_module = module.get_bsm_global_module(module.BSM_GLOBAL_MODULE_MENU)
        result = getattr(menu_module, module.BSM_GLOBAL_MODULE_MENU_MANAGE, None)

        by_role = getattr(settings, 'BSM_MANAGE_MENU_BY_ROLE', False)
        if not by_role:
            return result['default']
        else:
            groups = {
                item.name
                for item in user.groups.all()
            }
            if not groups:
                return []

            for item in groups:
                if item in result:
                    return result[item]

        return []

    @staticmethod
    def _get_menu_from_autobuild():
        """根据模型自定义菜单"""
        export_apps = get_export_apps()
        if not export_apps:
            return []
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
            return result
        except Exception:
            return []

    def filter_valid_menu(self, menus):
        return [{**m, 'children': self.filter_valid_menu(m['children'])} for m in menus if m.get('page', None) or m['children']]

    @staticmethod
    def get_menu_from_database(user):
        """从数据库中获取菜单"""
        # permissions = self.request.user.get_all_permissions()
        # permission_filter = (Q(permission=None) | Q(permission='') | Q(permission__in=permissions))
        menus = Menu.objects.order_by('sequence', 'id') if user.is_superuser else \
            Menu.objects.filter(Q(groups__in=user.groups.all()) | Q(groups__isnull=True)).order_by('sequence', 'id')
        fields = {field.name for field in Menu._meta.fields} - {'id', 'parent',  'permission', 'name', 'puzzle'}
        menus_map = {menu.id: dict({field: getattr(menu, field) for field in fields}, **{'name': menu.display_name, 'parent_id': menu.parent_id, 'children': [], 'puzzle': menu.puzzle_id}) for menu in menus}
        for _, menu in menus_map.items():
            parent_id = menu['parent_id']
            if parent_id and parent_id in menus_map:
                menus_map[parent_id]['children'].append(menu)
        return [m for _, m in menus_map.items() if not m.get('parent_id')]

    def get_menu_data(self, request, **kwargs):
        menus = []
        user = request.user
        menutype = kwargs.get('menutype', 'database')
        if hasattr(settings, 'ADMIN_MENUS'):
            menus = self.get_menu_from_settings(user)
        elif menutype == 'database':
            menus = self.get_menu_from_database(user)
        elif menutype == 'custom':
            menus = self._get_menu_from_custom(user)
        elif menutype == 'autobuild':
            menus = self._get_menu_from_autobuild()
        return self.filter_valid_menu(menus)

    @staticmethod
    def get_menu_from_settings(user):
        group_names = user.groups.values_list('name', flat=True)
        group_names = set(group_names)

        def map_menus(menus):
            return [
                {**m, 'children': map_menus(m.get('children', []))}
                for m in menus if 'groups' not in m or user.is_superuser or set(m['groups']) & group_names
            ]
        return map_menus(settings.ADMIN_MENUS)


def get_json_field_admin_config(json_object_schemas:dict, json_array_item_schemas:dict):
    """
    生成默认的json field admin
    :param json_object_schemas:
    :param json_array_item_schemas
    :return:
    """
    admin_configs = {}
    for key, value in json_object_schemas.items():
        admin_configs[key] = {'formFields': [field['name'] for field in value['fields']]}

    for key, value in json_array_item_schemas.items():
        admin_configs[key] = {'inlineFormFields': [field['name'] for field in value['fields']]}

    return admin_configs