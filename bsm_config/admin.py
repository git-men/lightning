from django.apps import apps
from django.contrib import admin

app_list = ['bsm_config']

for app_name in app_list:
    application = apps.get_app_config(app_name)
    admin.site.register(application.get_models())
