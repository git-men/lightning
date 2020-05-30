from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import Menu, Setting

MODEL_PAGES = (Menu.PAGE_LIST, Menu.PAGE_DETAIL)
ORDER_PAGES = (Menu.PAGE_ADMIN_CONFIG, Menu.PAGE_AUTO, Menu.PAGE_CHART, Menu.PAGE_IFRAME)

def create_permission(menu):
    if menu.page in MODEL_PAGES:
        app, model = menu.model.split('__')
        permission = Permission.objects.filter(content_type__app_label=app,content_type__model=model,codename=f'view_{model}').first()
     
    if menu.page in ORDER_PAGES or menu.type == Menu.TYPE_GROUP:
        codename = f'menu_view_{menu.page or menu.type}_{menu.id}'   
        content_type = ContentType.objects.get_for_model(Menu)
        permission, _ = Permission.objects.get_or_create(codename=codename, name=codename,content_type=content_type)
    
    permission.group_set.set(menu.groups.all())
    return f'{permission.content_type.app_label}.{permission.codename}'

def remove_permission(menu):
    if not menu.permission:
        return
    _ , codename = menu.permission.split('.')

    if menu.page in MODEL_PAGES:
        app, model = menu.model.split('__')
        isinstance = apps.get_app_config(app).get_model(model) 
        content_type = ContentType.objects.get_for_model(isinstance)
    else:    
        content_type = ContentType.objects.get_for_model(Menu)

    permission = Permission.objects.get(codename=codename, content_type=content_type)
    permission.group_set.clear()

    if menu.page in ORDER_PAGES:
        permission.delete()


def check_page(old_page, new_page):
    page1 = MODEL_PAGES
    page2 = ORDER_PAGES

    if (old_page in page1 and new_page in page1) or (old_page in page2 and new_page in page2):
        return False
    else:
        return True

def create_menus_permission(menus):
    permissions = []
    for menu in menus:
        if menu.page in MODEL_PAGES:
            app, model = menu.model.split('__')
            permission =f'{app}.view_{model}'

        if menu.page in ORDER_PAGES or menu.type == Menu.TYPE_GROUP:
            codename = f'menu_view_{menu.page or menu.type}_{menu.id}'   
            content_type = ContentType.objects.get_for_model(Menu)
            p = Permission(codename=codename, name=codename,content_type=content_type)
            permission = f'{p.content_type.app_label}.{p.codename}'
            permissions.append(p)
        
        menu.permission = permission

    Menu.objects.bulk_update(menus, ['permission'])
    Permission.objects.bulk_create(permissions)



    