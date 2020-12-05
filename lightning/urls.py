import os
import re
from django.http import HttpResponse
from django.template import engines
from django.urls import re_path, path, include
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.views import serve
from django.conf import settings

static_url = settings.STATIC_URL
lightning_static_url = getattr(settings, 'LIGHTNING_STATIC_URL', 'lightning')

index_template = open(finders.find(lightning_static_url + '/index.html')).read()
index_content = engines['django'].from_string(index_template).render({'public_path': static_url + lightning_static_url})
index_response = HttpResponse(index_content)


def index_view(request):
    return index_response


def is_relative_to(sub_path, dir_path):
    # 避免 path traversal 问题 https://owasp.org/www-community/attacks/Path_Traversal
    # Python 3.9 才有 Path.is_relative_to，
    # 而 Path.resolve 会 follow symbol link，
    # Path.absolute 又不能解析“../”，
    # 所以只能用 os.path.abspath 了
    return os.path.abspath(sub_path).startswith(os.path.abspath(dir_path))


urlpatterns = [
    path('basebone/storage/', include('storage.urls')),
    path('', include('api_basebone.urls')),
    re_path(r'^%s(?P<path>.*)$' % re.escape(static_url.lstrip('/')), serve, kwargs={'insecure': True}),
    re_path('^(?!basebone).*$', index_view)
]
