import sys
import os
from django.contrib.auth import get_user_model
from django.apps import AppConfig
from django.conf import settings
from api_basebone.utils import module


class LightningConfig(AppConfig):
    name = 'lightning'

    def ready(self):
        user_model = get_user_model()
        path = user_model._meta.app_config.name + '.bsm.' + module.BSM_FORM
        from .bsm import user_forms
        sys.modules[path] = user_forms

        apps = settings.INSTALLED_APPS
        for app in apps:
            app_module = __import__(app)
            path = app_module.__path__[0]
            functions_path = os.path.join(path, 'functions')
            signal_path = os.path.join(path, 'signals')
            if os.path.exists(functions_path + '.py'):
                __import__('.'.join([app, 'functions']))
            if os.path.exists(signal_path + '.py'):
                __import__('.'.join([app, 'signals']))
