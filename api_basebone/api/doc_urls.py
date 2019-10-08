from api_basebone.drf.routers import BaseBoneSimpleRouter as SimpleRouter
from api_basebone.api.doc_views import ApiDocViewSet

router = SimpleRouter(custom_base_name='api_doc')
router.register('', ApiDocViewSet)

urlpatterns = router.urls
