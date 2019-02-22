from rest_framework import fields


class ExportBooleanField(fields.BooleanField):
    """重新定义导出字段，使其符合中国人阅读习惯"""

    def to_representation(self, value):
        if value in self.TRUE_VALUES:
            return '是'
        elif value in self.FALSE_VALUES:
            return '否'
        return bool(value)
