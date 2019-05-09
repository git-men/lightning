from api_basebone.core.admin import BSMAdmin, register
from api_basebone.core.widgets import widgets

from bsm_config.models import Menu

@register
class MenuAdmin(BSMAdmin):
    display = ['icon', 'name', 'path', 'permission', 'content_type.app_label', 'content_type.model']
    filter = ['name', 'permission', 'path']
    form_fields = [
        'name', 'icon', 'parent', 'path', 'permission', 'content_type'
    ]
    display_in_tree = True  # 树型列表
