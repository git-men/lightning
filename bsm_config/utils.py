from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import Menu, Setting

MODEL_PAGES = (Menu.PAGE_LIST, Menu.PAGE_DETAIL, Menu.PAGE_MAP)
ORDER_PAGES = (Menu.PAGE_ADMIN_CONFIG,  Menu.PAGE_AUTO, Menu.PAGE_CHART, Menu.PAGE_IFRAME, Menu.PAGE_PUZZLE)

def remove_permission(menu):
    # 删除菜单权限
    permission, _ = get_permission(menu)
    if menu.page in ORDER_PAGES or menu.type == Menu.TYPE_GROUP:
        permission.delete()



# 检查页面、菜单类型是否更改
def check_page(old_page, new_page, old_type, new_type):
    page1 = MODEL_PAGES
    page2 = ORDER_PAGES
    if old_type == new_type == Menu.TYPE_GROUP:
        return False

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

def get_permission(menu):
    if menu.page in MODEL_PAGES:
        app, model = menu.model.split('__')
    content_model = Menu

    if not menu.permission:
        # 创建菜单权限
        if menu.page in MODEL_PAGES:
            content_model = apps.get_app_config(app).get_model(model)
            content_type = ContentType.objects.get_for_model(content_model)
            permission, _ = Permission.objects.get_or_create(codename=f'view_{model}', content_type=content_type)
     
        if menu.page in ORDER_PAGES or menu.type == Menu.TYPE_GROUP:
            codename = f'menu_view_{menu.page or menu.type}_{menu.id}'   
            content_type = ContentType.objects.get_for_model(content_model)
            permission, _ = Permission.objects.get_or_create(codename=codename, name=codename, content_type=content_type)

    else:
        # 通过menu.permission字符串获取权限实例
        _ , codename = menu.permission.split('.')
        if menu.page in MODEL_PAGES:
            try:
                content_model = apps.get_app_config(app).get_model(model)
            except Exception:
                return False, False
        # 代理模型不用for_concrete_model会返回代理指向的模型
        content_type = ContentType.objects.get_for_model(content_model, for_concrete_model=False)
        permission = Permission.objects.get(codename=codename, content_type=content_type)
    
    return permission,  f'{permission.content_type.app_label}.{permission.codename}'






    