import logging
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from .models import Menu, Admin
from .utils import remove_permission, check_page, get_permission
from api_basebone.signals import post_bsm_create, post_bsm_delete
log = logging.getLogger(__name__)

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
    if permission:
        permission.group_set.remove(*instance.groups.all().exclude(name='系统管理员'))
        remove_permission(instance)

from django.db.models.signals import m2m_changed
from django.contrib.auth.models import Permission, Group


@receiver(m2m_changed, sender=Menu.groups.through, dispatch_uid='menu_changed')
def menu_changed(sender, instance, model, pk_set, action, **kwargs):
    if model==Group and action in ('post_add', 'post_remove'):
        groups = model.objects.filter(pk__in=list(pk_set))
        print(sender, instance, model, pk_set, action, kwargs)
        permission, _ = get_permission(instance)
        if action == 'post_add':
            permission.group_set.add(*groups)
        if action == 'post_remove':
            permission.group_set.remove(*groups)


def create_inline_action_permission(app, model, config):
    """找到inlineAction中，有groups的配置。生成Permission，并与Groups产生并联。
    """
    if config.get('inlineActions', None) is None:
        return
    content_type = ContentType.objects.get(app_label=app, model=model)
    actions = [c for c in config['inlineActions'] if isinstance(c, dict) and 'groups' in c]
    for action in actions:
        permission = Permission(
            name=action['title'],
            codename=f'{action["type"]}_{model}_{action["id"]}',
            content_type=content_type
        )
        permission.save()
        if action['groups']:
            permission.group_set.set(action['groups'])


def update_inline_action_permission(app, model, new_config, old_config):
    """更新inlineAction,对比新旧内容。新的、相同的使用新配置，旧的删除掉。
    """
    new_actions, old_actions = set([]), set([])
    if new_config.get('inlineActions', None):
        actions = [c for c in new_config['inlineActions'] if isinstance(c, dict) and 'groups' in c]
        new_actions = set([action['id'] for action in actions])
    if old_config.get('inlineActions', None):
        actions = [c for c in old_config['inlineActions'] if isinstance(c, dict) and 'groups' in c]
        old_actions = set([action['id'] for action in actions])
    create = [action for action in new_config.get('inlineActions', []) if action['id'] in list(new_actions - old_actions)]
    update = [action for action in new_config.get('inlineActions', []) if action['id'] in list(new_actions & old_actions)]
    delete = [action for action in old_config.get('inlineActions', []) if action['id'] in list(old_actions - new_actions)]
    log.debug(f'ations of create: {create}, update: {update}, delete: {delete}')
    content_type = ContentType.objects.get(app_label=app, model=model)

    if create:
        ids = [action['id'] for action in create]
        actions = [action for action in new_config.get('inlineActions', []) if action['id'] in ids]
        for action in actions:
            log.debug(f'create permission for action: {action}')
            permission = Permission(
                name=action['title'],
                codename=f'{action["type"]}_{model}_{action["id"]}',
                content_type=content_type
            )
            permission.save()
            if action['groups']:
                permission.group_set.set(action['groups'])
    
    if update:
        ids = [action['id'] for action in update]
        actions = [action for action in new_config.get('inlineActions', []) if action['id'] in ids]
        for action in actions:
            log.debug(f'update permission for action: {action}')
            try:
                permission = Permission.objects.get(
                    codename=f'{action["type"]}_{model}_{action["id"]}',
                    content_type=content_type
                )
                if permission.name != action['title']:
                    permission.name = action['title']
                    permission.save()
                permission.group_set.set(action['groups'])
            except Permission.DoesNotExist:
                log.error('update and set permission error', exc_info=True)
                permission = Permission(
                    name=action['title'],
                    codename=f'{action["type"]}_{model}_{action["id"]}',
                    content_type=content_type
                )
                permission.save()
                if action['groups']:
                    log.debug(f'groups: {action["groups"]}')
                    permission.group_set.set(action['groups'])  # TODO 没有生效。 

    if delete:
        ids = [action['id'] for action in delete]
        actions = [action for action in old_config.get('inlineActions', []) if action['id'] in ids]
        for action in actions:
            log.debug(f'delete permission for action: {action}')
            try:
                permission = Permission.objects.get(
                    codename=f'{action["type"]}_{model}_{action["id"]}',
                    content_type=content_type
                ).delete()
            except:
                log.warn('delete permission error, may be does not exist')


def delete_inline_action_permission(app, model, config):
    if config.get('inlineActions', None):
        content_type = ContentType.objects.get(app_label=app, model=model)
        actions = [c for c in config['inlineActions'] if isinstance(c, dict) and 'groups' in c]
        filtered_actions = [f'{action["title"]}_{model}_{action["id"]}' for action in actions]
        Permission.objects.filter(code_name__in=filtered_actions, content_type=content_type).delete()


@receiver(post_bsm_create, sender=Admin, dispatch_uid='bsm_admin_change')
def admin_change(sender, instance, create, request, old_instance, **kwargs):
    """Admin修改了
    """
    # 1. InlineAction对应的权限生成与修改。
    if create:
        log.debug('Admin create')
        create_inline_action_permission(*instance.model.split('__'), instance.config)
    else:
        log.debug('Admin update')
        update_inline_action_permission(*instance.model.split('__'), instance.config, old_instance.config)

@receiver(post_bsm_delete, sender=Admin, dispatch_uid='bsm_admin_delete')
def admin_deleted(sender, instance, **kwargs):
    """Admin配置删除了
    """
    # 1. InlineAction对应权限的删除
    delete_inline_action_permission(*instance.model.split('__'), instance.config)