AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api_basebone.drf.handler.exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api_basebone.drf.authentication.CsrfExemptSessionAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
}
