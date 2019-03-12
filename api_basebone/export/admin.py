from django.apps import apps

from api_basebone.core.admin import VALID_MANAGE_ATTRS, BSM_BATCH_ACTION
from api_basebone.restful.batch_actions import get_model_batch_actions
from api_basebone.core.admin import BSMAdminModule
from api_basebone.utils import meta
from api_basebone.utils.format import underline_to_camel


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

    # 动态加载 amdin 模块
    meta.load_custom_admin_module()

    for key, cls in BSMAdminModule.modules.items():
        config[key] = bsm_admin_config.admin_model_config(cls)
    return config
