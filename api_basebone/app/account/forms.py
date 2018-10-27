from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.hashers import make_password

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


class UserCreateUpdateForm(serializers.ModelSerializer):
    """默认的用户序列化类"""

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'required': False
            }
        }

    def create(self, validated_data):
        """创建"""
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """更新"""
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance = super().update(instance, validated_data)
            instance.set_password(password)
            instance.save(update_fields=['password'])
        else:
            instance = super().update(instance, validated_data)
        return instance
