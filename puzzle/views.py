from rest_framework.decorators import api_view
from api_basebone.drf.response import success_response
from . import component_resolver_map, services
from .models import Block


@api_view()
def block_view(request, block_id):
    block = Block.objects.get(id=block_id)
    data = None
    if block.component in component_resolver_map:
        data = component_resolver_map[block.component](block)
    return success_response(data)


@api_view(['PUT'])
def move(request, block_id):
    parent = request.data.get('parent', None)
    index = request.data['index']
    services.move(block_id, parent, index)
    return success_response()
