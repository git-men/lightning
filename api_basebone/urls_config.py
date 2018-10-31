from django.urls import path, include

from .drf.routers import BaseBoneSimpleRouter as SimpleRouter
from .views import ConfigViewSet

router = SimpleRouter(custom_base_name='schema-config')
router.register('', ConfigViewSet)

urlpatterns = router.urls
