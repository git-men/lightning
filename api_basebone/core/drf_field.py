import arrow
import json

from django.conf import settings
from django.utils import six

from rest_framework import fields
from rest_framework.fields import JSONField as OriginJSONField


class ExportBooleanField(fields.BooleanField):
    """重新定义导出字段，使其符合中国人阅读习惯"""

    def to_representation(self, value):
        if value in self.TRUE_VALUES:
            return '是'
        elif value in self.FALSE_VALUES:
            return '否'
        return bool(value)


class ExportChoiceField(fields.ChoiceField):
    def to_representation(self, value):
        choices = self.parent.Meta.model._meta.get_field(self.field_name).choices

        if not choices:
            return super().to_representation(value)

        data_map = {item[0]: item[1] for item in choices}

        return super().to_representation(data_map.get(value, value))


class ExportDateTimeField(fields.DateTimeField):
    """
    格式化时间格式，使其符合阅读的习惯
    """

    def to_representation(self, value):
        if not value:
            return ''

        return arrow.get(value).to(settings.TIME_ZONE).format('YYYY-MM-DD HH:mm:ss')


class JSONField(OriginJSONField):
    """
    增强版的 JSONField
    """

    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, 'is_json_string', False):
                if isinstance(data, six.binary_type):
                    data = data.decode('utf-8')
                return json.loads(data)
            elif isinstance(data, str):
                result = json.loads(data)
                if not isinstance(result, (dict, list)):
                    self.fail('invalid')
                return result
            else:
                json.dumps(data)
        except (TypeError, ValueError):
            self.fail('invalid')
        return data

    def to_representation(self, value):
        if self.binary:
            value = json.dumps(value)
            # On python 2.x the return type for json.dumps() is underspecified.
            # On python 3.x json.dumps() returns unicode strings.
            if isinstance(value, six.text_type):
                value = bytes(value.encode('utf-8'))

        if isinstance(value, str):
            value = json.loads(value)
        return value
