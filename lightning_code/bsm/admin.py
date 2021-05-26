from django.conf import settings
from api_basebone.core.admin import BSMAdmin, register
from lightning_code.models import Category, Tag, Function, Parameter

@register
class CategoryAdmin(BSMAdmin):
    form_fields = ['code', 'name', 'parent', 'description']
    detail = {
        'style': 'group',
        'showNav': True,
        'sections': [
            {
                'title': '函数列表',
                'fields': [{'name': 'functions', 'widget': 'refDetail'}],
                'style': {}
            }
        ]
    }

    class Meta:
        model = Category

@register
class FunctionAdmin(BSMAdmin):
    filter = ['scope', 'category', 'tags']
    modal_form = False
    display = ['name', 'scope', 'language', 'enable', 'tags', 'update_time']
    form_fields = ['name', 'scope', 'language', 'enable', 
        {'name': 'tags', 'params': {'canAdd': True}},
        {'name': 'parameters', 'widget': 'InnerTable', 'params': {'canAdd': True}},
        'return_type', 
        {'name': 'return_type_ref', 'widget': 'ModelSelect', 'show': '${return_type} === "ref"'},
        {'name': 'code', 'widget': 'CodeEditor', 'params': {'firstLineNumber': 3}}        
    ]
    inline_actions = ['edit', 'delete']

    class Meta:
        model = Function

@register
class ParameterAdmin(BSMAdmin):
    display = ['name', 'display_name', 'type', 'ref', 'required', 'description']
    form_fields = [
        'name', 'display_name', 'type',
        {'name': 'ref', 'widget': 'ModelSelect', 'show': '${type} === "ref"'},
        'required', 'description'
    ]
    class Meta:
        model = Parameter

