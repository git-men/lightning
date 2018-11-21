from django.apps import apps

INSTALLED_APP_MAP = {
    app.label: app.name
    for app in apps.get_app_configs()
}


def get_app(app_slug):
    """
    根据 app_slug 获取应用的名称

    例如可以根据 auth 获取返回 django.contrib.auth
    """
    return INSTALLED_APP_MAP.get(app_slug)
