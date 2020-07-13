from django.contrib.contenttypes.models import ContentType

from api_basebone.core.admin import BSMAdmin, register
from api_basebone.core.widgets import widgets

from bsm_config.models import Menu, Admin

@register
class MenuAdmin(BSMAdmin):
    display = [
        {
            'widget': 'iconText',
            'fields': {
                'icon': 'icon',
                'text': 'display_name',
            },
            'displayName': '名称'
        },
        'page', 'model',
    ]
    form_fields = [
        'name', 
        {'name': 'icon', 'widget': 'IconSelect'},
        {'name': 'parent', 'widget': 'Cascader'},
        {'name': 'type', 'widget': 'Radio'},
        {'name': 'page', 'show': '${type} === "item"'},
        {'name': 'model', 'widget': 'ModelSelect', 'show': '(${page} === "list" || ${page} === "detail") && ${type} === "item"'},
        {'name': 'path', 'show': '${page} === "auto" || ${page} === "iframe"'},
        'groups'
    ]
    inlineFormFields = ['sequence']
    display_in_tree = True  # 树型列表
    display_in_sort = True # 排序列表
    sort_key = 'sequence' # 排序字段
    inline_actions = ['edit', 'delete']

    class Meta:
        model = Menu

@register
class AdminConfigAdmin(BSMAdmin):
    display = ['model', {'name': "config", 'fields': {'value': "config"}, 'widget': "longtext", 'textType': "jsonText"}]
    form_fields = [
        'model',
        {'name': "config", 'widget': "JsonEditor"}
    ]
    inline_actions = ['edit']

    class Meta:
        model = Admin

# @register
# class PermissionAdmin(BSMAdmin):
#     display = ['']
#     class Meta:
#         model = Permission


class ContentType(BSMAdmin):
    
    class Meta:
        model = ContentType
