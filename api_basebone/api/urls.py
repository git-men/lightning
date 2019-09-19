# from django.urls import path
# from api_basebone.api import views

# urlpatterns = [path('<str:slug>/', views.api_run, name='api_run')]

# from api_basebone.drf.routers import SimpleRouter as ApiRouter

from .routers import ApiRouter
from .views import ApiViewSet


router = ApiRouter(custom_base_name='api')

router.register('', ApiViewSet)

urlpatterns = router.urls
