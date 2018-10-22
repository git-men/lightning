"""
动作

种类的动作可以应对各种场合，即约定型的操作

例如批量动作可以批量删除，批量更新，批量创建，甚至是批量中可以支持多种动作的混合
"""

from rest_framework import serializers
from api_basebone.core import exceptions


class deleteForm(serializers.Serializer):
    key = serializers.CharField(max_length=20)
    data = serializers.ListField(min_length=1)

    def validate(self, attrs):
        model = self.context.get('view').model
        key, data = attrs['key'], attrs['data']
        filter_params = {f'{key}__in': data}

        if len(data) != model.objects.filter(**filter_params).count():
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                error_message='列表中包含不合法的数据'
            )
        return attrs

    def handle(self):
        """动作执行"""
        model = self.context.get('view').model
        key, data = self.validated_data['key'], self.validated_data['data']
        filter_params = {f'{key}__in': data}

        model.objects.filter(**filter_params).delete()
