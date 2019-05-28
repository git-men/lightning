from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from api_basebone.core.admin import BSMAdmin, register
from api_basebone.core.widgets import widgets

from bsm_config.models import Menu

@register
class MenuAdmin(BSMAdmin):
    display = [
        {
            'type': 'combo',
            'name': 'displayName',
            'displayName': '名称',
            'template': 'iconText',
            'mapping': {'icon': 'icon', 'text': 'name'}
        },
        'page', 'permission', 'model', 'sequence']
    form_fields = [
        'name', 'icon', 'parent', 'page', 'permission', 'model', 'sequence'
    ]
    inlineFormFields = ['sequence']
    display_in_tree = True  # 树型列表

    class Meta:
        model = Menu


# @register
# class PermissionAdmin(BSMAdmin):
#     display = ['']
#     class Meta:
#         model = Permission


class ContentType(BSMAdmin):
    
    class Meta:
        model = ContentType