from django.db import models
from jsonfield import JSONField as OriginJSONField
from rest_framework.fields import JSONField as DrfJSONField
from rest_framework import fields
from rest_framework.serializers import ModelSerializer
from api_basebone.core import drf_field
from api_basebone.core.fields import JSONField
from api_basebone.export.fields import DJANGO_FIELD_TYPE_MAP


class CharIntegerField(fields.IntegerField):

    def to_representation(self, value):
        return f'{value}'


def get_serializer_class(field_class):
    bsm_custom = {
        JSONField: drf_field.JSONField,
        OriginJSONField: DrfJSONField,
        models.BooleanField: fields.BooleanField,
        models.DateTimeField: fields.DateTimeField,
    }
    if field_class in bsm_custom:
        return bsm_custom[field_class]
    if field_class in ModelSerializer.serializer_field_mapping:
        return ModelSerializer.serializer_field_mapping[field_class]
    return ModelSerializer.serializer_field_mapping[models.TextField]


class BSMFieldMixin:
    to_type = None

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        for k, v in instance.to_type.deconstruct()[-1].items():
            setattr(instance, k, v)

        if cls not in ModelSerializer.serializer_field_mapping or cls.__name__ not in DJANGO_FIELD_TYPE_MAP:
            if instance.to_type is not None:
                to = instance.to_type.__class__
            else:
                for to in cls.mro():
                    if to not in [cls, BSMFieldMixin]:
                        break

            class FieldSerializerMixin(get_serializer_class(to)):
                def to_internal_value(self, value):
                    return cls.bsm_to_internal_value(self, value)

                def to_representation(self, value):
                    return cls.bsm_to_representation(self, value)

            ModelSerializer.serializer_field_mapping[cls] = FieldSerializerMixin
            DJANGO_FIELD_TYPE_MAP[cls.__name__] = DJANGO_FIELD_TYPE_MAP[instance.get_to_field()]
        return instance

    def get_bsm_internal_type(self):
        return self.__class__.__name__

    def get_to_field(self):
        if self.to_type is not None:
            if hasattr(self.to_type, 'get_bsm_internal_type'):
                return self.to_type.gsm_bsm_internal_type()
            else:
                return self.to_type.get_internal_type()
        elif hasattr(self, 'get_bsm_internal_type'):
            return self.get_bsm_internal_type()
        else:
            return self.get_internal_type()

    def bsm_to_internal_value(self, value):
        print(value, 'bsm_to_internal_value', repr(value))
        return value

    def bsm_to_representation(self, value):
        print(value, 'bsm_to_representation', repr(value))
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
