from django.urls import path, include

from .drf.routers import SimpleRouter
from .views import CommonManageViewSet

router = SimpleRouter(custom_base_name='common-manage')
router.register('', CommonManageViewSet)

urlpatterns = router.urls
