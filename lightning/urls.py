import os
from pathlib import Path
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.template import engines
from django.urls import re_path, path, include
from django.conf import settings

static_path = Path(__file__).absolute().parent.joinpath('static')
static_url = settings.STATIC_URL

index_template = static_path.joinpath('lightning/index.html').open().read()
index_content = engines['django'].from_string(index_template).render({'public_path': static_url})
index_response = HttpResponse(index_content)


def is_relative_to(sub_path, dir_path):
    # 避免 path traversal 问题 https://owasp.org/www-community/attacks/Path_Traversal
    # Python 3.9 才有 Path.is_relative_to，
    # 而 Path.resolve 会 follow symbol link，
    # Path.absolute 又不能解析“../”，
    # 所以只能用 os.path.abspath 了
    return os.path.abspath(sub_path).startswith(os.path.abspath(dir_path))


def asset_view(request, asset_path):
    p = static_path.joinpath(asset_path)
    if not is_relative_to(p, static_path) or not p.is_file():
        return HttpResponseNotFound()
    return FileResponse(p.open('rb'))


def index_view(request, sub_path):
    su = static_url[1:]
    if sub_path.startswith(su):
        return asset_view(request, sub_path[len(su):])
    return index_response


urlpatterns = [
    path('basebone/storage/', include('storage.urls')),
    path('', include('api_basebone.urls')),
    re_path('^(?!basebone)(?P<sub_path>.*$)', index_view)
]
