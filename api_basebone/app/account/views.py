from django.contrib.auth import get_user_model, logout
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api_basebone.drf.response import success_response
from api_basebone.restful.serializers import create_serializer_class
from . import forms


class ManageAccountViewSet(viewsets.GenericViewSet):
    """通用管理端账号接口"""

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        model = get_user_model()
        return create_serializer_class(model)

    @action(detail=False, url_path='userinfo')
    def get_userinfo(self, request, *args, **kwargs):
        """
        ## 检测是否是否登录

        如果用户已登录，则直接返回此登录用户的数据结构
        """
        serializer = self.get_serializer(request.user)
        result = {}
        result.update(serializer.data)
        result['permissions'] = request.user.get_all_permissions()
        return success_response(result)

    @action(methods=['post'], detail=False)
    def logout(self, request, *args, **kwargs):
        """退出登录"""
        logout(request)
        return success_response()

    @action(methods=['post'], detail=False, permission_classes=())
    def login(self, request, *args, **kwargs):
        """
        ## 用户登录

        ```
        Params:
            username string 用户名
            password string 用户密码

        Returns:
            object 用户数据结构
        ```
        """
        serializer = forms.LoginForm(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    @action(methods=['get'], detail=False)
    def permissions(self, request, *args, **kwargs):
        """获取当前用户的权限
        """
        return success_response(request.user.get_all_permissions())
