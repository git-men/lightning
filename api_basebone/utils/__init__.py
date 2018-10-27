from django.conf import settings


INSTALLED_APP_MAP = {
    item.split('.')[-1]: item
    for item in settings.INSTALLED_APPS
}


def get_app(slug):
    return INSTALLED_APP_MAP.get(slug)
