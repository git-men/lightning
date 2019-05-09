from api_basebone.core.admin import BSMAdmin, register
from api_basebone.core.widgets import widgets

from bsm_config.models import Menu

@register
class MenuAdmin(BSMAdmin):
    display = ['icon', 'name', 'page', 'permission', 'model']
    filter = ['name', 'permission', 'page']
    form_fields = [
        'name', 'icon', 'parent', 'page', 'permission', 'model'
    ]
    display_in_tree = True  # 树型列表

    class Meta:
        model = Menu
