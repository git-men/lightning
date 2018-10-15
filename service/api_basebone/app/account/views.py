from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action

from api_basebone.drf.response import success_response


class ManageAccountViewSet(viewsets.GenericViewSet):
    """通用管理端账号接口"""

    permission_classes = (permissions.IsAuthenticated, )

    @action(methods=['post'], detail=False)
    def logout(self, request):
        """退出登录"""
        logout(request)
        return success_response()
