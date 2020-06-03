from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group

from .models import Menu
from .utils import remove_permission, check_page, get_permission

@receiver(pre_save, sender=Menu, dispatch_uid='remove_menu_permission')
def remove_menu_permission(sender, instance, update_fields = [], **kwargs):
    if instance.id:
        old_instance = Menu.objects.get(id=instance.id)
        old_page = old_instance.page
        new_page = instance.page
        old_type = old_instance.type
        new_type = instance.type

        if check_page(old_page, new_page, old_type, new_type):
            remove_permission(old_instance)

        if new_page not in (Menu.PAGE_LIST, Menu.PAGE_DETAIL):
            instance.model = ''
    

@receiver(post_save, sender=Menu, dispatch_uid='set_menu_permission')
def set_menu_permission(sender, instance, update_fields = [], **kwargs):
    _, permission_lable = get_permission(instance)
    Menu.objects.filter(id=instance.id).update(permission=permission_lable)

@receiver(pre_delete, sender=Menu, dispatch_uid='delete_menu_permission')
def delete_menu_permission(sender, instance, **kwargs):
    permission, _ = get_permission(instance)
    permission.group_set.remove(*instance.groups.all().exclude(name='系统管理员'))
    remove_permission(instance)

from django.db.models.signals import m2m_changed
from django.contrib.auth.models import Permission, Group


def menu_changed(instance, model, pk_set, action, **kwargs):
    # raise Exception('jfsdfjsdaa')
    if action in ('post_add', 'post_remove'):
        # menu = Menu.objects.get(sender.menu_id)
        groups = model.objects.filter(pk__in=list(pk_set))
        permission, _ = get_permission(instance)
        if action == 'post_add':
            permission.group_set.add(*groups)
        if action == 'post_remove':
            permission.group_set.remove(*groups)
m2m_changed.connect(menu_changed, sender=Menu.groups.through)