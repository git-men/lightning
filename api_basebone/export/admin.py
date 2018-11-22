from django.apps import apps

from api_basebone.core.admin import VALID_MANAGE_ATTRS, BSM_BATCH_ACTION
from api_basebone.restful.batch_actions import get_model_batch_actions

from api_basebone.utils import meta
from api_basebone.utils.format import underline_to_camel


def admin_model_config(model):
    """获取指定模型对应的 admin 的配置"""
    config, module = {}, meta.get_bsm_model_admin(model)
    if not module:
        return

    for item in dir(module):
        if item in VALID_MANAGE_ATTRS:
            config[underline_to_camel(item)] = getattr(module, item, None)

    model_actions = get_model_batch_actions(model)
    if model_actions:
        config[BSM_BATCH_ACTION] = [
            [key, getattr(value, 'short_description', key)]
            for key, value in model_actions.items()
        ]

    return {
        f'{model._meta.app_label}__{model._meta.model_name}': config
    }


def get_app_admin_config():
    """获取应用管理端的配置"""
    export_apps, config = meta.get_export_apps(), {}
    if not export_apps:
        return config

    # 动态加载 amdin 模块
    meta.load_custom_admin_module()
    for item in export_apps:
        app = apps.get_app_config(item)
        for model in app.get_models():
            model_admin_config = admin_model_config(model)
            if model_admin_config:
                config.update(model_admin_config)
    return config
