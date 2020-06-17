from django.db import transaction
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model

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
def update_setting(user, settings, **kwargs):
    result = {}
    with transaction.atomic():
        for key, value in settings.items():
            setting = Setting.objects.filter(key=key)
            if setting.exists():
                setting.update(key=key, value= value)
                result.update({setting.first().key: setting.first().value}) 

    return  result

@bsm_func(staff_required=True, name='update_user', model=Setting)
def update_user(user=None, **kwargs):
    id = kwargs.get('id', None)
    username = kwargs.get('username', None)
    old_passWord = kwargs.get('oldPassWord', None)
    new_passWord = kwargs.get('newPassWord', None)
    user = User.objects.get(id=id)
    if user.check_password(old_passWord):
        user.set_password(new_passWord)
        user.username = username
        user.save()
    else:
        raise RuntimeError('old password error')
    

@bsm_func(staff_required=True, name='get_assign_permissions', model=Permission)
def get_assign_permissions(user, **kwargs):
    permissions = get_objects_for_user(user, 'auth.permission_assign').select_related('content_type')
    serializer_class = multiple_create_serializer_class( 
        Permission, 
        expand_fields=['content_type'], 
    ) 
    return [serializer_class(per).data for per in permissions ]