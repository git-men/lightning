from django.db import transaction
from django.conf import settings as SETTINGS
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import get_objects_for_user

from api_basebone.restful.funcs import bsm_func
from bsm_config.models import Setting
from api_basebone.restful.serializers import multiple_create_serializer_class

User = get_user_model()

def init_setting():
    settings = [
        {'key':'logo', 'value': None, 'type': 'image', 'display_name': '网站LOGO'},
        {'key':'title', 'value': '闪电管理后台', 'type': 'string', 'display_name': '网站标题'}
    ]
    for setting_conf in settings:
        setting = Setting(**setting_conf)
        setting.save()

@bsm_func(staff_required=True, name='update_setting', model=Setting)
def update_setting(user, settings, model, **kwargs):
    result = {}
    with transaction.atomic():
        for key, value in settings.items():
            setting, create = Setting.objects.get_or_create(key=key)
            setting.value_json = {'value':value}
            setting.save()
            result.update({setting.key: setting.value}) 
    return  result

@bsm_func(staff_required=True, name='update_user_password', model=Setting)
def update_user(user, **kwargs):
    id = kwargs.get('id', None)
    old_passWord = kwargs.get('oldPassWord', None)
    new_passWord = kwargs.get('newPassWord', None)
    if user.check_password(old_passWord):
        user.set_password(new_passWord)
        user.save()
    else:
        raise RuntimeError('旧密码错误')
    

@bsm_func(staff_required=True, name='get_assign_permissions', model=Permission)
def get_assign_permissions(user, **kwargs):
    permissions = get_objects_for_user(user, 'auth.permission_assign').select_related('content_type')
    serializer_class = multiple_create_serializer_class( 
        Permission, 
        expand_fields=['content_type'], 
    ) 
    return [serializer_class(per).data for per in permissions ]