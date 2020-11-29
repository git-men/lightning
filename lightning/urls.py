from pathlib import Path

from django.http import FileResponse, HttpResponseNotFound
from django.urls import re_path, path, include
from django.conf import settings

static_path = getattr(settings, 'LIGHTING_STATIC_PATH', Path(__file__).absolute().parent.joinpath('static'))


def index_view(request):
    return FileResponse(static_path.joinpath('index.html').open('rb'))


def asset_view(request, asset_path):
    p = static_path.joinpath(asset_path)
    if not p.is_file():
        return HttpResponseNotFound()
    return FileResponse(p.open('rb'))


urlpatterns = [
    path('basebone/block/', include('puzzle.urls')),
    path('basebone/storage/', include('storage.urls')),
    re_path(r'^lightning/(?P<asset_path>.*$)', asset_view),
    path('', include('api_basebone.urls')),
    re_path('^(?!basebone).*$', index_view)
]
