from django.db import transaction
from django.contrib.auth.models import User

from api_basebone.restful.funcs import bsm_func
from bsm_config.models import Setting
from api_basebone.drf.response import success_response, error_response

def init_setting():
    settings = [
        {'key':'logo', 'value': None, 'type': 'image', 'display_name': '网站LOGO'},
        {'key':'title', 'value': '闪电管理后台', 'type': 'string', 'display_name': '网站标题'}
    ]
    for setting_conf in settings:
        setting = Setting(**setting_conf)
        setting.save()

@bsm_func(staff_required=True, name='update_setting', model=Setting)
def update_setting(user=None, **kwargs):
    print('---------------setting----------')
    print(kwargs)
    settings = dict(kwargs)
    del settings['view_context']
    print(settings)
    result = {}
    with transaction.atomic():
        for key, value in settings.items():
            setting = Setting.objects.filter(key=key)
            print(11,setting)
            if setting.exists():
                setting.update(key=key, value= value)
                print('---------')
                print(setting)
                result.update({setting.first().key: setting.first().value}) 

    print(1111,result)
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
