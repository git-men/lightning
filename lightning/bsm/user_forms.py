from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from api_basebone.restful.forms import create_form_class


User = get_user_model()
UserDefaultSerialzier = create_form_class(User)
password_field = User._meta.get_field('password')


class UserCreateClientForm(UserDefaultSerialzier):
    """客户端创建用户的表单"""

    class Meta(UserDefaultSerialzier.Meta):
        extra_kwargs = {
            'password': {
                'required': False
            }
        }

    def create(self, validated_data):
        """创建"""
        validated_data['password'] = make_password(validated_data['password'])
        user = User(**validated_data)
        user.save()  # 触发 post_save signal
        return user


class UserUpdateClientForm(UserDefaultSerialzier):
    """客户端更新用户的表单"""

    class Meta(UserDefaultSerialzier.Meta):
        extra_kwargs = {
            'password': {
                'required': False
            }
        }

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            instance.save(update_fields=['password'])
        return instance


class UserCreateManageForm(UserDefaultSerialzier):
    """创建用户的表单"""

    def create(self, validated_data):
        validated_data.setdefault('is_staff', True)
        instance = super().create(validated_data)
        instance.set_password(validated_data['password'])
        instance.save(update_fields=['password'])
        return instance


class UserUpdateManageForm(UserDefaultSerialzier):

    password = serializers.CharField(
        max_length=password_field.max_length,
        allow_blank=True, allow_null=False, required=False
    )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            instance.save(update_fields=['password'])
        return instance


class AdminUserCreateManageForm(UserCreateManageForm):
    pass


class AdminUserUpdateManageForm(UserUpdateManageForm):
    pass