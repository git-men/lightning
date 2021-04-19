import logging
import uuid

from django.db.models.signals import post_save, pre_delete, pre_save, post_migrate
from django.db.models import Min
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from bsm_config.models import Menu, Admin, Setting
from .utils import remove_permission, check_page, get_permission, MODEL_PAGES
from .settings import WEBSITE_CONFIG
from api_basebone.signals import post_bsm_create, post_bsm_delete
from api_basebone.core import admin
log = logging.getLogger(__name__)

@receiver(pre_save, sender=Menu, dispatch_uid='remove_menu_permission')
def remove_menu_permission(sender, instance, update_fields = [], **kwargs):
    if instance._state.adding:
        """把新建的菜单排序到最前面"""
        min_sequence = Menu.objects.exclude(sequence=0).values_list('sequence', flat=True).annotate(Min('sequence')).order_by('sequence').first() or 1000
        instance.sequence = min_sequence - 1
    else:
        old_instance = Menu.objects.get(id=instance.id)
        old_page = old_instance.page
        new_page = instance.page
        old_type = old_instance.type
        new_type = instance.type

        if check_page(old_page, new_page, old_type, new_type):
            remove_permission(old_instance)
            # 清空permission
            instance.permission = ''

        if new_page not in MODEL_PAGES:
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

@receiver(post_migrate)
def update_setting_config_permission(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(Setting)
    permissions = [*Permission.objects.filter(content_type=content_type).values_list('codename', flat=True)]
    permission_assign_content_type = ContentType.objects.get_for_model(Permission)
    Permission.objects.get_or_create(content_type=permission_assign_content_type, codename='permission_assign', name='权限分配')
    for setting in WEBSITE_CONFIG:
        codename = setting.get('permission_code',None)
        if codename and (codename not in permissions):
            name = setting.get('title',None) or setting.get('key',None)
            per = Permission.objects.create(content_type=content_type, codename=codename, name=name)
            system_group =  Group.objects.filter(name='系统管理员').first()
            if system_group:
                per.group_set.add(system_group)
                from guardian.shortcuts import assign_perm
                assign_perm('auth.permission_assign', system_group,  obj=per)


def get_actions(config):
    result = []
    for action in config.get('inlineActions', []) + config.get('actions', []) + config.get('tableActions', []):
        if not isinstance(action, dict):
            action = {'action': action}
        if 'id' not in action:
            action['id'] = str(uuid.uuid4().hex)
        result.append(action)
    return result


def create_action_permission(app, model, config):
    """找到inlineAction中，有groups的配置。生成Permission，并与Groups产生并联。
    """
    actions = get_actions(config)
    if not actions:
        return
    content_type = ContentType.objects.get(app_label=app, model=model)
    actions = [c for c in actions if isinstance(c, dict) and 'groups' in c]
    for action in actions:
        permission = Permission(
            name=action['title'],
            codename=f'{action["type"]}_{model}_{action["id"]}',
            content_type=content_type
        )
        permission.save()
        if action['groups']:
            permission.group_set.set(action['groups'])


def update_action_permission(app, model, new_config, old_config):
    """更新inlineAction,对比新旧内容。新的、相同的使用新配置，旧的删除掉。
    """
    new_action_ids, old_action_ids = set([]), set([])
    new_actions = get_actions(new_config)
    old_actions = get_actions(old_config)
    if new_actions:
        actions = [c for c in new_actions if isinstance(c, dict) and 'groups' in c]
        new_action_ids = set([action['id'] for action in actions])
    if old_actions:
        actions = [c for c in old_actions if isinstance(c, dict) and 'groups' in c]
        old_action_ids = set([action['id'] for action in actions])
    create = [action for action in new_actions if action['id'] in list(new_action_ids - old_action_ids)]
    update = [action for action in new_actions if action['id'] in list(new_action_ids & old_action_ids)]
    delete = [action for action in old_actions if isinstance(action, dict) and action['id'] in list(old_action_ids - new_action_ids)]
    log.debug(f'ations of create: {create}, update: {update}, delete: {delete}')
    content_type = ContentType.objects.get(app_label=app, model=model)

    if create:
        ids = [action['id'] for action in create]
        actions = [action for action in new_actions if action['id'] in ids]
        for action in actions:
            log.debug(f'create permission for action: {action}')
            permission = Permission(
                # 适配tableAction的格式
                name=action.get('title', None) or action['name'],
                codename=f'{action.get("action") or action["type"]}_{model}_{action["id"]}',
                content_type=content_type
            )
            permission.save()
            if action['groups']:
                # 适配tableAction的格式
                permission.group_set.set([a['id'] if isinstance(a, dict) else a for a in action['groups']])
    
    if update:
        ids = [action['id'] for action in update]
        actions = [action for action in new_actions if action['id'] in ids]
        for action in actions:
            log.debug(f'update permission for action: {action}')
            try:
                permission = Permission.objects.get(
                # 适配tableAction的格式
                    codename=f'{action.get("action") or action["type"]}_{model}_{action["id"]}',
                    content_type=content_type
                )
                if permission.name != action.get('title', action.get('name', '')):
                    permission.name = action.get('title', action.get('name', ''))
                    permission.save()
                # 适配tableAction的格式
                permission.group_set.set([a['id'] if isinstance(a, dict) else a for a in action['groups']])
            except Permission.DoesNotExist:
                log.error('update and set permission error', exc_info=True)
                permission = Permission(
                    name=action.get('title', action.get('name', '')),
                    codename=f'{action["action"]}_{model}_{action["id"]}',
                    content_type=content_type
                )
                permission.save()
                if action['groups']:
                    log.debug(f'groups: {action["groups"]}')
                    permission.group_set.set(action['groups'])  # TODO 没有生效。 

    if delete:
        ids = [action['id'] for action in delete]
        actions = [action for action in old_actions if action['id'] in ids]
        for action in actions:
            log.debug(f'delete permission for action: {action}')
            try:
                permission = Permission.objects.get(
                    codename=f'{action["action"]}_{model}_{action["id"]}',
                    content_type=content_type
                ).delete()
            except:
                log.warn('delete permission error, may be does not exist')


def delete_action_permission(app, model, config):
    if get_actions(config):
        content_type = ContentType.objects.get(app_label=app, model=model)
        actions = [c for c in get_actions(config) if isinstance(c, dict) and 'groups' in c]
        filtered_actions = [f'{action["action"]}_{model}_{action["id"]}' for action in actions]
        Permission.objects.filter(code_name__in=filtered_actions, content_type=content_type).delete()


@receiver(post_bsm_create, sender=Admin, dispatch_uid='bsm_admin_change')
def admin_change(sender, instance, create, request, old_instance, **kwargs):
    """Admin修改了
    """
    # 1. InlineAction对应的权限生成与修改。
    if create:
        log.debug('Admin create')
        create_action_permission(*instance.model.split('__'), instance.config)
    else:
        log.debug('Admin update')
        update_action_permission(*instance.model.split('__'), instance.config, old_instance.config)
    admin.set_config(instance.model, instance.config)

@receiver(post_bsm_delete, sender=Admin, dispatch_uid='bsm_admin_delete')
def admin_deleted(sender, instance, **kwargs):
    """Admin配置删除了
    """
    # 1. InlineAction对应权限的删除
    delete_action_permission(*instance.model.split('__'), instance.config)
    admin.set_config(instance.model, None)
