from django.apps import apps

from api_basebone.batch_actions import get_model_action
from api_basebone.core.admin import VALID_MANAGE_ATTRS, BSM_BATCH_ACTION
from api_basebone.utils.meta import get_export_apps, get_bsm_model_admin, get_bsm_app_admin
from api_basebone.utils.format import underline_to_camel


def admin_model_config(model):
    """获取模型对应的 admin 的配置"""

    config = {}
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    module = get_bsm_model_admin(model)

    if module:
        for item in dir(module):
            if item in VALID_MANAGE_ATTRS:
                config[underline_to_camel(item)] = getattr(module, item, None)

    # 转换 action
    model_actions = get_model_action(model)
    if model_actions:
        config[BSM_BATCH_ACTION] = [
            [key, getattr(value, 'short_description', key)]
            for key, value in model_actions.items()
        ]

    return {
        key: config
    }


def load_admin_module():
    """加载 admin 的 module"""
    export_apps = get_export_apps()
    if not export_apps:
        return
    for app_label in export_apps:
        get_bsm_app_admin(app_label)


def get_app_admin_config():
    """获取应用管理的配置"""
    export_apps = get_export_apps()
    config = {}
    if not export_apps:
        return config

    for item in export_apps:
        try:
            app = apps.get_app_config(item)
            for m in app.get_models():
                config.update(admin_model_config(m))
        except Exception:
            pass
    return config
