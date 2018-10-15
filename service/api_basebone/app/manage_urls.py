from api_basebone.drf.routers import SimpleRouter
from .account.views import ManageAccountViewSet


router = SimpleRouter(custom_base_name='basebone-app')

router.register('account', ManageAccountViewSet)

urlpatterns = router.urls
