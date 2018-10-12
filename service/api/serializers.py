from rest_framework import serializers


class BaseModelSerializerMixin:
    """通用的序列化类的抽象"""

    class Meta:
        fields = '__all__'

    def to_representation(self, instance):
        result = super().to_representation(instance)
        request = self.context.get('request')

        display_fields = request.data.get('display_fields')
        if display_fields and isinstance(display_fields, list):
            return {
                key: result[key]
                for key in display_fields
            }
        return result
