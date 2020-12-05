import re
from django.urls import re_path, path, include
from django.contrib.staticfiles.views import serve
from django.conf import settings
from . import views

urlpatterns = [
    path('basebone/storage/', include('storage.urls')),
    path('', include('api_basebone.urls')),
    re_path(r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/')), serve, kwargs={'insecure': True}),
    re_path('^(?!basebone).*$', views.index_view)
]
