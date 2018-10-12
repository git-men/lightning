from rest_framework import viewsets
from utils.api_response import success_response


class CommonManageViewSet(viewsets.ModelViewSet):
    """通用的管理接口视图"""

    def get_queryset(self):
        """动态的计算结果集"""

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        return queryset

    def get_serializer_class(self):
        """动态的计算序列化类"""
        return self.serializer_class

    def list(self, request, **kwargs):
        print(kwargs)
        print('hello world')
        return success_response({'age': 23, 'name': 'kycool'})
