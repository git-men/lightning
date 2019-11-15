from api_basebone.drf.routers import BaseBoneSimpleRouter as SimpleRouter
from api_basebone.restful.client.views import CommonManageViewSet as ClientViewSet

router = SimpleRouter(custom_base_name='common-client')
router.register('', ClientViewSet)

urlpatterns = router.urls
