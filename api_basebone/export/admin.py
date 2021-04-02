from api_basebone.core.admin import VALID_MANAGE_ATTRS, BSM_BATCH_ACTION
from api_basebone.restful.batch_actions import get_model_batch_actions
from api_basebone.core.admin import BSMAdminModule
from api_basebone.utils import meta
from api_basebone.utils.format import underline_to_camel
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

    def admin_model_config(self, cls):
        """获取指定模型对应的 admin 的配置"""

        config = {}
        model = cls.Meta.model

        for item in dir(cls):
            if item in VALID_MANAGE_ATTRS:
                config[underline_to_camel(item)] = getattr(cls, item, None)

        if BSM_BATCH_ACTION not in config:
            model_actions = get_model_batch_actions(model)
            if model_actions:
                config[BSM_BATCH_ACTION] = [
                    [key, getattr(value, 'short_description', key)]
                    for key, value in model_actions.items()
                ]

        return config

bsm_admin_config = BSMAdminConfig()


def get_app_admin_config():
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
        config[key] = bsm_admin_config.admin_model_config(cls)
    return config


class ExportService:
    def get_app_admin_config(self, request=None):
        return get_app_admin_config()


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