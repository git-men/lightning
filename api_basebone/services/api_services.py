import logging

from django.apps import apps

from api_basebone.export.fields import get_model_field_config

from ..api import const
from ..api import po
from ..api import utils

log = logging.getLogger(__name__)


def save_api(config):
    driver = utils.get_api_driver()
    return driver.save_api(config)


def show_api(slug):
    driver = utils.get_api_driver()
    config = driver.get_api_config(slug)
    return config


def get_api_po(slug):
    config = show_api(slug)
    api = po.loadAPIFromConfig(config)
    return api


def list_api(app=None):
    driver = utils.get_api_driver()
    return driver.list_api_config()


def get_all_api_po():
    api_list = list_api()
    po_list = []
    for config in api_list:
        po = get_api_po(config['slug'])
        po_list.append(po)
    return po_list


def get_api_schema_models():
    apis = get_all_api_po()
    models = set()
    for api in apis:
        display_fields = api.displayfield
        if display_fields:
            '''有查询属性的不需要schema'''
            continue
        if api.operation in (
            const.OPERATION_UPDATE_BY_CONDITION,
            const.OPERATION_DELETE_BY_CONDITION,
            const.OPERATION_FUNC,
            const.OPERATION_DELETE,
        ):
            '''不返回schema对象的也不需要'''
            continue
        app = api.app
        model_name = api.model
        model = apps.get_model(app, model_name)
        if model is None:
            continue
        if model in models:
            continue
        models.add(model)
        add_api_ref_models(models, model)

    return list(models)


def add_api_ref_models(models, model_class):
    field_configs = get_model_field_config(model_class)
    for model_name, d in field_configs.items():
        for f in d['fields']:
            if f['type'] in ('ref', 'mref'):
                refs = f['ref'].split('__')
                if len(refs) < 2:
                    continue
                app = refs[0]
                model_name = refs[1]
                model_class = apps.get_model(app, model_name)
                if model_class in models:
                    continue
                models.add(model_class)
                add_api_ref_models(models, model_class)

