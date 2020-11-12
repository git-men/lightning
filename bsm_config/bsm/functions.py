from django.db import transaction
from django.conf import settings as SETTINGS
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import get_objects_for_user

from api_basebone.restful.funcs import bsm_func
from bsm_config.models import Setting, FieldPermission, Admin, FieldAdmin
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
            setting, create = Setting.objects.get_or_create(key=key)
            setting.value = value
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



@bsm_func(staff_required=True, name='update_field_permission', model=FieldPermission)
def update_field_permission(user, model, permissions, **kwargs):
    admin, admin_created = Admin.objects.get_or_create(model=model)
    field_permissions = []
    with transaction.atomic():
        for permission in permissions:
            field = permission['field']
            field_admin, field_admin_created = FieldAdmin.objects.get_or_create(admin=admin, field=field)
            group = permission['group']
            read = permission.get('read', False)
            write = permission.get('write', False)
            field_permission, field_permission_created = FieldPermission.objects.get_or_create(field_admin=field_admin, group_id=group)
            field_permission.read = write if write else read
            field_permission.write = write
            field_permissions.append(field_permission)

    if field_permissions:
        FieldPermission.objects.bulk_update(field_permissions, ['read', 'write'])


        
@bsm_func(staff_required=True, name='get_field_permissions', model=FieldPermission)
def get_field_permissions(user, model, **kwargs):
    field_admins = FieldAdmin.objects.filter(admin__model=model).prefetch_related('fieldpermission_set')
    next_permissions = []
    for field_admin in field_admins:
        for fieldpermission in field_admin.fieldpermission_set.all():
            permission = {}
            permission['field'] = field_admin.field
            permission['group'] = fieldpermission.group.id
            permission['read'] = fieldpermission.read
            permission['write'] = fieldpermission.write
            next_permissions.append(permission)
    return next_permissions 