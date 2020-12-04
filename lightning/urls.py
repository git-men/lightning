from pathlib import Path

from django.http import HttpResponse
from django.template import engines
from django.urls import re_path, path, include
from django.conf import settings

index_template = Path(__file__).absolute().parent.joinpath('static').joinpath('lightning/index.html').open().read()
index_content = engines['django'].from_string(index_template).render({'public_path': settings.STATIC_URL[:-1]})
index_response = HttpResponse(index_content)

urlpatterns = [
    path('basebone/storage/', include('storage.urls')),
    path('', include('api_basebone.urls')),
    re_path('^(?!basebone).*$', lambda r: index_response)
]
