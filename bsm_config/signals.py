from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group

from .models import Menu
from .utils import create_permission, remove_permission, check_page

@receiver(pre_save, sender=Menu, dispatch_uid='remove_menu_permission')
def remove_menu_permission(sender, instance, update_fields = [], **kwargs):
    if instance.id:
        old_instance = Menu.objects.get(id=instance.id)
        old_page = old_instance.page
        new_page = instance.page

        if check_page(old_page, new_page):
            remove_permission(old_instance)

        if new_page not in (Menu.PAGE_LIST, Menu.PAGE_DETAIL):
            instance.model = ''
    

@receiver(post_save, sender=Menu, dispatch_uid='set_menu_permission')
def set_menu_permission(sender, instance, update_fields = [], **kwargs):
    permission = create_permission(instance)
    Menu.objects.filter(id=instance.id).update(permission=permission)

@receiver(pre_delete, sender=Menu, dispatch_uid='delete_menu_permission')
def delete_menu_permission(sender, instance, **kwargs):
    remove_permission(instance)
        