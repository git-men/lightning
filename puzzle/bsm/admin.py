from api_basebone.core.admin import BSMAdmin, register
from .. import models


@register
class BlockAdmin(BSMAdmin):
    filter = ['id', 'parent', 'component']
    display = ['id', 'component']
    display_in_tree = True
    form_fields = ['id', {'name': 'parent', 'widget': 'Cascader'}, 'component']
    inline_actions = ['edit', 'delete']

    @staticmethod
    def get_queryset(queryset, request, view):
        if 'root' in request.data:
            return models.Block.objects.get(id=request.data['root']).get_descendants(include_self=True)
        return queryset

    class Meta:
        model = models.Block


@register
class PageAdmin(BlockAdmin):
    filter = BlockAdmin.filter + ['name']
    display = BlockAdmin.display + ['name']
    form_fields = BlockAdmin.form_fields + ['name']

    class Meta:
        model = models.Page
