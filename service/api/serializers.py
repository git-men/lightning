import imaplib
from rest_framework import serializers


class BaseModelSerializerMixin:
    """通用的序列化类的抽象"""

    class Meta:
        fields = '__all__'

    def to_representation(self, instance):
        """
        根据客户端传入的展示字段列表进行筛选和解析
        """
        result = super().to_representation(instance)
        request = self.context.get('request')

        display_fields = request.data.get('display_fields')
        if display_fields and isinstance(display_fields, list):
            return {
                key: result[key]
                for key in display_fields
            }

        # expand_fields = request.data.get('expand_fields')
        return result


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta"""

    attrs = {
        'model': model,
        'fields': '__all__'
    }
    if exclude_fields is not None:
        attrs['exclude'] = exclude_fields

    return type('Meta', (object, ), attrs)


def create_serializer_class(model, exclude_fields=None, **kwargs):
    """构建序列化类"""

    attrs = {
        'Meta': create_meta_class(model, exclude_fields=None)
    }
    attrs.update(kwargs)

    class_name = f'{model}ModelSerializer'
    return type(
        class_name,
        (BaseModelSerializerMixin, serializers.ModelSerializer, ),
        attrs
    )
