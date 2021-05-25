from api_basebone.core.admin import BSMAdmin
from api_basebone.core.admin import BSMAdminModule
from api_basebone.utils import meta
from bsm_config.models import Admin
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
    def get_app_admin_config(self, request=None):
        return get_app_admin_config(request)


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