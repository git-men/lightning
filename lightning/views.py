import json
import functools

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import engines
from django.contrib.staticfiles import finders
from django.conf import settings
from rest_framework.utils import encoders

from api_basebone.export.fields import get_app_field_schema
from api_basebone.export.menu import get_menu_data
from api_basebone.export.setting import get_settins
from api_basebone.restful.serializers import create_serializer_class

lightning_static_url = getattr(settings, 'LIGHTNING_STATIC_URL', 'lightning')
static_url = settings.STATIC_URL
public_path = getattr(settings, 'LIGHTNING_CDN_HOST', '').rstrip('/') + static_url + lightning_static_url

index_template = open(finders.find(lightning_static_url + '/index.html')).read()
index_template = engines['django'].from_string(index_template)


def get_userinfo(user):
    model = get_user_model()
    serializer_class = create_serializer_class(model)
    serializer = serializer_class(user)
    return serializer.data


# def adapt_decorator_to_method(d):
#     return lambda method: functools.wraps(method)(lambda self, *args, **kwargs:  d(lambda *a, **k: method(self, *a, **k))(*args, **kwargs))


def adapt_high_order_decorator_to_method(b):
    return lambda *args, **kwargs: lambda method: functools.wraps(method)(lambda self, *method_arg, **method_kwargs: b(*args, **kwargs)(lambda *a, **k: method(self, *a, **k))(*method_arg, **method_kwargs))


login_required = adapt_high_order_decorator_to_method(login_required)


class LightningView:
    def __init__(self, lightning_context):
        self.lightning_context = lightning_context

    @property
    def export_service(self):
        return self.lightning_context.export

    @login_required(redirect_field_name='redirect', login_url='/user/login')
    def index_view(self, request):
        user = request.user
        index_content = index_template.render({
            'public_path': public_path,
            'injection': json.dumps({
                '$$schemas': get_app_field_schema(),
                '$$admins': self.export_service.get_app_admin_config(request),
                '$$menus': get_menu_data(user),
                '$$settings': get_settins(),
                '$$userinfo': get_userinfo(user),
                '$$permissions': user.get_all_permissions(),
            }, cls=encoders.JSONEncoder),  # encoders.JSONEncoder 解决django lazy object不能json.dumps的问题
        })
        return HttpResponse(index_content)

    @staticmethod
    def login_page(request):
        index_content = index_template.render({
            'public_path': public_path,
            'injection': json.dumps({
            }, cls=encoders.JSONEncoder),  # encoders.JSONEncoder 解决django lazy object不能json.dumps的问题
        })
        return HttpResponse(index_content)
