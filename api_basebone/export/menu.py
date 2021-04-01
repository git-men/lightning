from django.conf import settings
from django.db.models import Q
from bsm_config.models import Menu


def get_menu_from_database(user):
    """从数据库中获取菜单"""
    # permissions = self.request.user.get_all_permissions()
    # permission_filter = (Q(permission=None) | Q(permission='') | Q(permission__in=permissions))
    menus =  Menu.objects.order_by('sequence','id') if user.is_superuser else \
        Menu.objects.filter(Q(groups__in=user.groups.all()) | Q(groups__isnull=True)).order_by('sequence','id')
    fields =  { field.name for field in Menu._meta.fields } - {'id', 'parent',  'permission', 'name', 'puzzle'}
    menus_map = { menu.id: dict({ field: getattr(menu, field) for field in fields }, **{ 'name': menu.display_name, 'parent_id': menu.parent_id, 'children': [], 'puzzle': menu.puzzle_id }) for menu in menus }
    for _, menu in menus_map.items():
        parent_id = menu['parent_id']
        if parent_id and parent_id in menus_map:
            menus_map[parent_id]['children'].append(menu)
    return [m for _, m in menus_map.items() if not m.get('parent_id')]


def filter_valid_menu(menus):
    return [{**m, 'children': filter_valid_menu(m['children'])} for m in menus if m['page'] or m['children']]


def get_menu_data(user):
    if hasattr(settings, 'ADMIN_MENUS'):
        menus = get_menu_from_settings(user)
    else:
        menus = get_menu_from_database(user)
    return filter_valid_menu(menus)


def get_menu_from_settings(user):
    group_names = user.groups.values_list('name', flat=True)
    group_names = set(group_names)

    def map_menus(menus):
        return [
            {**m, 'children': map_menus(m.get('children', []))}
            for m in menus if 'groups' not in m or user.is_superuser or set(m['groups']) & group_names
        ]
    return map_menus(settings.ADMIN_MENUS)
