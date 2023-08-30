from django.conf import settings


def conf(label, default):
    return getattr(settings, 'LIGHTNING_' + label, default)


NUMERIC_RESPONSE_STATUS = conf('NUMERIC_RESPONSE_STATUS', False)
BUILTIN_ADMIN = conf('BUILTIN_ADMIN', True)
QUERYSET_VERSION = conf('QUERYSET_VERSION', 'v1')
