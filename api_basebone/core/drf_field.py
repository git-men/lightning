import arrow

from django.conf import settings
from rest_framework import fields


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

        data_map = {
            item[0]: item[1] for item in choices
        }

        return super().to_representation(data_map.get(value, value))


class ExportDateTimeField(fields.DateTimeField):
    """
    格式化时间格式，使其符合阅读的习惯
    """
    def to_representation(self, value):
        if not value:
            return ''

        return arrow.get(value).to(settings.TIME_ZONE).format(
            'YYYY-MM-DD HH:mm:ss'
        )
