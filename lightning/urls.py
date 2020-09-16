from pathlib import Path

from django.http import FileResponse
from django.urls import re_path

static_path = Path(__file__).absolute().parent.joinpath('static')


def index_view(request):
    p = static_path.joinpath(request.path[1:])
    if p.is_dir():
        p = p.joinpath('index.html')
    if not p.exists():
        p = static_path.joinpath('index.html')
    return FileResponse(p.open('rb'))


urlpatterns = [
    re_path('.*', index_view)
]
