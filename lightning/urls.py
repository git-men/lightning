import re
from django.urls import re_path, path, include
from django.contrib.staticfiles.views import serve
from django.conf import settings
from .views import LightningView
from .services import Lightning
from oauth2_provider.models import *

lightning_static_url = getattr(settings, 'LIGHTNING_STATIC_URL', 'lightning')

FRONT_END_ROUTES = [
    '',
    'user',
    'user/login',
    'user/register',
    'user/qrcode_login',
    'user/install',
    'login/qrcode_login',
    'lightning',
    'account/settings',
    'account/settings',
    'dashboard/charts',
    'puzzle/.*',
    'content/.*',
    'config/admin',
    'iframe/.*',
]


class LightningRoute:
    def __init__(self, lightning_context=None):
        if lightning_context:
            self.lightning_context = lightning_context
        else:
            self.lightning_context = Lightning()
        self.views = LightningView(self.lightning_context)

    @property
    def urls(self):
        return [
            path('basebone/oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
            path('basebone/block/', include('puzzle.urls')),
            path('basebone/storage/', include('storage.urls')),
            path('', include('api_basebone.urls')),
            re_path(r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/')), serve, kwargs={'insecure': True}),
            path('user/login', self.views.login_page),
            path('index.html', self.views.login_page),
            path('basebone/manifest.json', self.views.manifest),
            path('service-worker.js', self.views.service_worker),
            path('basebone/index.html', self.views.login_page),
            re_path(r'^basebone/precache-manifest\.\w+\.js$', self.views.precache_manifest),
        ] + [re_path('^{}$'.format(r), self.views.index_view) for r in FRONT_END_ROUTES]


lightning = Lightning()
urlpatterns = lightning.urls
