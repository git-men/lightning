from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from api_basebone.core.admin import BSMAdmin, register
from api_basebone.core.widgets import widgets

from bsm_config.models import Menu

@register
class MenuAdmin(BSMAdmin):
    display = [
        # {
        #     'type': 'combo',
        #     'name': 'displayName',
        #     'displayName': '名称',
        #     'template': 'iconText',
        #     'mapping': {'icon': 'icon', 'text': 'name'}
        # },
        'name','page', 'permission', 'model', 'sequence']
    form_fields = [
        'name', 'icon',
        {'name': 'parent', 'widget': 'Cascader'},
        'page',
        {'name': 'model', 'show': '${page} === "list" || ${page} === "detail"'},
        'permission', 'sequence',
        {'name': 'path', 'show': '${page} === "auto"'}
    ]
    inlineFormFields = ['sequence']
    display_in_tree = True  # 树型列表
    display_in_sort = True # 排序列表
    sort_key = 'sequence' # 排序字段
    inline_actions = ['edit', 'delete']

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