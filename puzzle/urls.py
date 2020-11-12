from django.urls import path
from . import views

urlpatterns = [
    path('<block_id>', views.block_view),
    path('<block_id>/move', views.move),
]
