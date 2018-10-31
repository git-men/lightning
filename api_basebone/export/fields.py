import inspect

from django.apps import apps
from django.db.models.fields import NOT_PROVIDED
from api_basebone.utils.meta import get_concrete_fields, get_export_apps

from .specs import FIELDS

DJANGO_FIELD_TYPE_MAP = {
    'AutoField': 'Integer',
    'BooleanField': 'Bool',
    'CharField': 'String',
    'DateField': 'Date',
    'EmailField': 'String',
    'DateTimeField': 'DateTime',
    'FloatField': 'Float',
    'IntegerField': 'Integer',
    'TextField': 'Text',
    'TimeField': 'Time',
    'URLField': 'string',
    'ForeignKey': 'Ref',
    'OneToOneField': 'Ref',
    'ManyToManyField': 'RefMult',
}


class FieldConfig:

    def _get_common_field_params(self, field, data_type):
        config = {
            'name': field.name,
            'displayName': field.verbose_name,
            'required': not field.blank,
            'type': data_type
        }

        if field.choices:
            config['choices'] = field.choices

        if not field.editable:
            config['editable'] = field.editable

        if field.default is not NOT_PROVIDED:
            if not inspect.isfunction(field.default):
                config['default'] = field.default

        return config

    def string_params(self, field, data_type):
        base = self._get_common_field_params(field, data_type)
        base['maxLength'] = field.max_length
        return base

    def ref_params(self, field, data_type):
        base = self._get_common_field_params(field, data_type)
        meta = field.related_model._meta
        base['ref'] = '{}__{}'.format(meta.app_label, meta.model_name)
        return base

    def refmult_params(self, field, data_type):
        base = self._get_common_field_params(field, data_type)
        meta = field.related_model._meta
        base['ref'] = '{}__{}'.format(meta.app_label, meta.model_name)
        return base


field_config = FieldConfig()


def get_model_field_config(model):
    fields = get_concrete_fields(model)
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)

    config = []
    for item in fields:
        field_type = DJANGO_FIELD_TYPE_MAP.get(item.get_internal_type(), None)
        if field_type is not None:
            data_type = FIELDS.get(field_type)['name']
            function = getattr(field_config, '{}_params'.format(field_type.lower()), None)
            if function is not None:
                config.append(function(item, data_type))
            else:
                config.append(field_config._get_common_field_params(item, data_type))

    return {
        key: {
            'name': key,
            'displayName': model._meta.verbose_name,
            'fields': config
        }
    }


def get_app_model_config():
    """获取应用模型配置"""
    export_apps = get_export_apps()
    config = {}

    for item in export_apps:
        try:
            app = apps.get_app_config(item)
            for m in app.get_models():
                config.update(get_model_field_config(m))
        except Exception:
            pass
    return config
