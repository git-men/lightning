from api_basebone.drf.routers import SimpleRouter
from .account.views import ManageAccountViewSet
from .upload import views as upload_views


router = SimpleRouter(custom_base_name='basebone-app')

router.register('account', ManageAccountViewSet)
router.register('upload', upload_views.UploadViewSet)

urlpatterns = router.urls
