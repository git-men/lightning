from django.apps import apps

from api_basebone.restful.manage.batch_actions import get_model_batch_actions
from api_basebone.core.admin import (
    VALID_MANAGE_ATTRS,
    BSM_BATCH_ACTION,
    BSMAdminModule,
)

from api_basebone.utils import meta
from api_basebone.utils.format import underline_to_camel


def admin_model_config(model):
    """获取模型对应的 admin 的配置"""

    config = {}

    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    module = BSMAdminModule.modules.get(key)

    if not module:
        return

    for item in dir(module):
        if item in VALID_MANAGE_ATTRS:
            config[underline_to_camel(item)] = getattr(module, item, None)

    # 转换 batch action
    model_actions = get_model_batch_actions(model)
    if model_actions:
        config[BSM_BATCH_ACTION] = [
            [key, getattr(value, 'short_description', key)]
            for key, value in model_actions.items()
        ]

    return {key: config}


def get_app_admin_config():
    """获取应用管理的配置"""
    export_apps = meta.get_export_apps()
    config = {}
    if not export_apps:
        return config

    # 动态加载配置
    meta.load_custom_admin_module()

    for item in export_apps:
        try:
            app = apps.get_app_config(item)
            for model in app.get_models():
                # 获取配置，如果配置为空，则不显示到最终的配置中去
                model_admin_config = admin_model_config(model)
                if model_admin_config:
                    config.update(model_admin_config)
        except Exception as e:
            print(f'get bsm model config exception: {item} {e}')
    return config
