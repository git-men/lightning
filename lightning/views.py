from django.http import HttpResponse
from django.template import engines
from django.contrib.staticfiles import finders
from django.conf import settings

lightning_static_url = getattr(settings, 'LIGHTNING_STATIC_URL', 'lightning')
static_url = settings.STATIC_URL

index_template = open(finders.find(lightning_static_url + '/index.html')).read()
index_content = engines['django'].from_string(index_template).render({'public_path': static_url + lightning_static_url})
index_response = HttpResponse(index_content)


def index_view(request):
    return index_response
