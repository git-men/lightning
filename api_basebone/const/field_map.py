from rest_framework import fields

from api_basebone.core import drf_field
from api_basebone.export.specs import FieldType

# 计算字段的类型和序列化字段的映射
ComputedFieldTypeSerializerMap = {
    FieldType.STRING: fields.CharField,
    FieldType.INTEGER: fields.IntegerField,
    FieldType.BOOL: fields.BooleanField,
    FieldType.TEXT: fields.CharField,
    FieldType.RICHTEXT: fields.CharField,
    FieldType.FLOAT: fields.FloatField,
    FieldType.DECIMAL: fields.DecimalField,
    FieldType.IMAGE: fields.CharField,
    FieldType.DATE: fields.DateField,
    FieldType.TIME: fields.TimeField,
    FieldType.DATETIME: fields.DateTimeField,
    FieldType.DURATION: fields.DurationField,
}

# 导出的字段和序列化字段的映射
ExportFieldTypeSerializerMap = {
    FieldType.BOOL: drf_field.ExportBooleanField,
    FieldType.DATETIME: drf_field.ExportDateTimeField,
}
