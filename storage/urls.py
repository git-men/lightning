from django.urls import path, re_path
from . import views

urlpatterns = [
    path('upload', views.upload),
    re_path(r'file/+(?P<key>.*)', views.file),
]
