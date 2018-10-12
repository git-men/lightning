from django.urls import path, include
from utils.routers import SimpleRouter

from .views import CommonManageViewSet

router = SimpleRouter(custom_base_name='common-manage')
router.register('data', CommonManageViewSet)

urlpatterns = router.urls
