from django.db import models
from jsonfield import JSONField as OriginJSONField
from rest_framework.fields import JSONField as DrfJSONField
from rest_framework import fields
from rest_framework.serializers import ModelSerializer
from rest_framework.utils.field_mapping import ClassLookupDict

from api_basebone.core import drf_field
from api_basebone.core.fields import JSONField, ArrayField
from api_basebone.export.fields import DJANGO_FIELD_TYPE_MAP


class CharIntegerField(fields.IntegerField):

    def to_representation(self, value):
        return f'{value}'


def get_serializer_class(field):
    bsm_custom = {
        **ModelSerializer.serializer_field_mapping,
        JSONField: drf_field.JSONField,
        OriginJSONField: DrfJSONField,
        models.BooleanField: fields.BooleanField,
        models.DateTimeField: fields.DateTimeField,
    }
    try:
        return ClassLookupDict(bsm_custom)[field]
    except:
        return fields.CharField


class BSMField:
    to_type = None

    def super_serializer(self):
        return get_serializer_class(self.to_type or self)

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if instance.to_type:
            for k, v in instance.to_type.deconstruct()[-1].items():
                setattr(instance, k, v)

        if cls not in ModelSerializer.serializer_field_mapping or cls.__name__ not in DJANGO_FIELD_TYPE_MAP:
            class BSMFieldSerializer(instance.super_serializer()):
                def to_internal_value(self, value):
                    return instance.bsm_to_internal_value(super().to_internal_value(value))

                def to_representation(self, value):
                    return super().to_representation(instance.bsm_to_representation(value))

            ModelSerializer.serializer_field_mapping[cls] = BSMFieldSerializer
            DJANGO_FIELD_TYPE_MAP[cls.__name__] = DJANGO_FIELD_TYPE_MAP[instance.get_to_field()]
        return instance

    def get_bsm_internal_type(self):
        return type(self).__name__

    def get_to_field(self):
        if self.to_type is not None:
            if hasattr(self.to_type, 'get_bsm_internal_type'):
                return self.to_type.get_bsm_internal_type()
            else:
                return self.to_type.get_internal_type()
        elif hasattr(self, 'get_bsm_internal_type'):
            return self.get_bsm_internal_type()
        else:
            return self.get_internal_type()

    def bsm_to_internal_value(self, value):
        return value

    def bsm_to_representation(self, value):
        return value


def define_bsm_field(base, to_type=None, to_internal_value=None, to_representation=None):
    if to_type is None:
        to_type = base()

    class FieldMixin:
        def __init__(self, *args, **kwargs):
            for k, v in to_type.deconstruct()[-1].items():
                setattr(self, k, v)
            super().__init__(*args, **kwargs)

        def get_bsm_internal_type(self):
            return self.__class__.__name__

    field_cls = type('BSM'+base.__name__, (FieldMixin, base,), {})

    class FieldSerializerMixin:
        def to_internal_value(self, value):
            print(value, 'to_internal_value', repr(value))
            return to_internal_value(value)

        def to_representation(self, value):
            print(value, 'to_representation', repr(value))
            return to_representation(value)

    ModelSerializer.serializer_field_mapping[field_cls] = type(field_cls.__name__, (FieldSerializerMixin, get_serializer_class(to_type.__class__,)), {})
    DJANGO_FIELD_TYPE_MAP[field_cls.__name__] = DJANGO_FIELD_TYPE_MAP[to_type.get_bsm_internal_type() if hasattr(to_type, 'get_bsm_internal_type') else to_type.get_internal_type()]

    return field_cls


class MultiReferField(BSMField, ArrayField):
    def __init__(self, *args, **kwargs):
        self.to_field = kwargs.pop('to_field')
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['to_field'] = self.to_field
        return name, path, args, kwargs

    def get_bsm_internal_type(self):
        return super(BSMField, self).get_bsm_internal_type()

    def bsm_to_internal_value(self, value):
        return [item if isinstance(item, str) else item[self.to_field] for item in value]

    def bsm_to_representation(self, value):
        return [{self.to_field: item, 'id': i} for i, item in enumerate(value)]
