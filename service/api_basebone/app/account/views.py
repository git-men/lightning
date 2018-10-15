from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.serializers import create_serializer_class
from . import forms


class ManageAccountViewSet(viewsets.GenericViewSet):
    """通用管理端账号接口"""

    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        model = get_user_model()
        return create_serializer_class(model)

    @action(methods=['post'], detail=False)
    def logout(self, request):
        """退出登录"""
        logout(request)
        return success_response()

    @action(methods=['post'], detail=False, permission_classes=())
    def login(self, request, *args, **kwargs):
        serializer = forms.LoginForm(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer)
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)
