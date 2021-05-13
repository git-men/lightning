import sys
import os
import logging
from django.contrib.auth import get_user_model
from django.apps import AppConfig
from django.conf import settings
from api_basebone.utils import module

log = logging.getLogger('lightning')


class LightningConfig(AppConfig):
    name = 'lightning'

    def ready(self):
        user_model = get_user_model()
        path = user_model._meta.app_config.name + '.bsm.' + module.BSM_FORM
        from .bsm import user_forms
        sys.modules[path] = user_forms

        apps = settings.INSTALLED_APPS
        for app in apps:
            try:
                # TODO INSTALLED_APPS 里配的内容不一定是module，还不一定是字符串。提前导入也会改变导入顺序，使一些云函数的覆盖逻辑出错。
                app_module = __import__(app)
                path = app_module.__path__[0]
                functions_path = os.path.join(path, 'functions')
                signal_path = os.path.join(path, 'signals')
                if os.path.exists(functions_path + '.py'):
                    __import__('.'.join([app, 'functions']))
                if os.path.exists(signal_path + '.py'):
                    __import__('.'.join([app, 'signals']))
            except:
                log.error(f'自动发现脚本发生异常: {functions_path}', exc_info=True)
                pass
