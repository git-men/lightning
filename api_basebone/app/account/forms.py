from django.contrib.auth import authenticate, login, get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

User = get_user_model()


class LoginForm(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=32)

    def validate(self, data):
        request = self.context['request']
        user = authenticate(request, **data)
        if not user:
            raise ValidationError({'password': '用户不存在或密码不正确'})

        login(request, user)
        return {'user': user}

    def create(self, validated_data):
        return validated_data['user']
