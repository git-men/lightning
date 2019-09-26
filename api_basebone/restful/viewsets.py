from rest_framework import viewsets
from rest_framework.decorators import action

from api_basebone.core import const
from api_basebone.services import rest_services


class BSMModelViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def list(self, request, *args, **kwargs):
        """获取列表数据"""
        display_fields = request.data.get(const.DISPLAY_FIELDS)
        return rest_services.display(self, display_fields)

    @action(methods=['POST'], detail=False, url_path='list')
    def set(self, request, app, model, **kwargs):
        """获取列表数据"""
        return self.list(request, app, model, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """获取数据详情"""
        display_fields = request.data.get(const.DISPLAY_FIELDS)
        return rest_services.retrieve(self, display_fields)

    def destroy(self, request, *args, **kwargs):
        """删除数据"""
        return rest_services.destroy(self, request)
