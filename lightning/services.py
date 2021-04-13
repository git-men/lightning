from django.contrib.auth import get_user_model
from django.db.models import TextField, URLField, AutoField, BigAutoField
from django.db import transaction
from django.apps import apps
from django.conf import settings

from api_basebone.export.admin import ExportService
from bsm_config.models import Menu, Admin
from bsm_config.utils import create_menus_permission
from bsm_config.settings import site_setting
from .const import DEFAULT_MENU

User = get_user_model()


def create_default_menu():
    menus_data = []
    menus_mapping = {}
    cust_menus = getattr(settings, 'LIGHTNING_MENUS', DEFAULT_MENU)
    for menu_data in cust_menus:
        default = dict(menu_data)
        children = menu_data.get('children', None)
        if children:
            for child_menu in children:
                menus_mapping.update({child_menu.get('name',None): menu_data.get('name',None)})
                child = dict(child_menu)
                child.pop("children")
                menus_data.append(Menu(**child))
        default.pop("children")
        menus_data.append(Menu(**default))
    Menu.objects.bulk_create(menus_data)

    all_menu = Menu.objects.all()
    update_menu = []
    for children, parent in menus_mapping.items():
        menu = all_menu.filter(name=children).first()
        menu.parent = all_menu.filter(name=parent).first()
        update_menu.append(menu)
    Menu.objects.bulk_update(update_menu, ['parent'])


def create_admin_config(app_labels, exist_model):
    """创建user_app下新增的model的admin、菜单和权限"""

    models = [model for model in apps.get_models() 
                if model._meta.app_label in app_labels and f'{model._meta.app_label}__{model._meta.model_name}' not in exist_model]

    menu_ids = list(Menu.objects.values_list('id', flat=True))
    menu_list = Menu.objects.all()
    menu_ids = [menu.id for menu in menu_list]
    menu_keys = [f'{menu.model}-{menu.page}' for menu in menu_list]
    admins = []
    menus = []
    permissions = []
    for model in models:
        key = '{}__{}'.format(model._meta.app_label, model._meta.model_name).lower()
        config = {'display':[], 'formFields':[], 'inlineActions':['edit', 'detail', 'delete'], 'filter':[]}
        detail = {'fields': False, 'sections':[],'style': 'group'}
        detailTableFields = []
        detailFields = []

        for field in model._meta.fields:
            if not (field.primary_key or field.many_to_many):  # 主键和多对多默认不在列表中显示
                config['display'].append(field.name)

            if not field.primary_key and type(field) not in [TextField, URLField]:
                config['filter'].append(field.name)

            if type(field) not in [AutoField, BigAutoField] or not(field.primary_key and type(field) in [AutoField, BigAutoField]):
                item = {"name": field.name}
                if field.many_to_one:
                    item['nestedForm'] = ['add','edit']
                config['formFields'].append(item)

            if type(field) in(TextField,):
                detailFields.append(field.name)
            elif not field.many_to_many:
                detailTableFields.append(field.name)

        if detailTableFields: 
            detail['sections'].append({'fields': detailTableFields,'style': {'widget': "tiles"}})
        if detailFields:
            for f in detailFields:
                detail['sections'].append({'fields':[f]})  
        config['details'] = [detail]

        admins.append(Admin(model=key, config=config)) 

        # 生成admin时顺便生成菜单
        # name = model.verbose_name or model.name
        menus.append(Menu(
            name= '', 
            model= key, 
            page='list',
            icon='unordered-list',
        ))
        # 生成admin时资源顺便关联默认角色
        app_name, model_name = key.split('__')
        permissions.append(f'{app_name}.view_{model_name}')
        permissions.append(f'{app_name}.delete_{model_name}')
        permissions.append(f'{app_name}.add_{model_name}')
        permissions.append(f'{app_name}.change_{model_name}')
    Admin.objects.bulk_create(admins)
    Menu.objects.bulk_create([menu for menu in menus if f'{menu.model}-{menu.page}' not in menu_keys])
    new_meus = Menu.objects.exclude(id__in=menu_ids)
    # 返回所有模型权限
    return permissions, new_meus


@transaction.atomic
def generate_configs(app_labels=[]):
    menus = Menu.objects.all()
    if not menus:
        create_default_menu()
        create_menus_permission(Menu.objects.all())
    
    admins = Admin.objects.all()
    old_models = []
    for app in app_labels:
        old_models = [admin.model for admin in admins if admin.model.startswith(f'{app}__')]
    new_permission, new_meus = create_admin_config(app_labels, old_models)
    if new_meus:
        # 创建新增菜单的资源
        create_menus_permission(new_meus)
    return new_permission, new_meus


class Lightning:
    export = ExportService()

    def __init__(self):
        from .urls import LightningRoute
        self.route = LightningRoute(self)
        self.site_setting = site_setting

    @property
    def urls(self):
        return self.route.urls


__all__ = ['Lightning']
