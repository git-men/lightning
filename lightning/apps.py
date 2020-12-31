import sys
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
            try:
                __import__('.'.join([app, 'functions']))
                __import__('.'.join([app, 'signals']))
            except:
                pass
        
