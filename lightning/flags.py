from django.conf import settings


def conf(label, default):
    return getattr(settings, 'LIGHTNING_' + label, default)


BUILTIN_ADMIN = conf('BUILTIN_ADMIN', True)
