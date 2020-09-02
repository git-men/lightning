import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from shield.filter import SHIELD_RULES_DICT_CACHE_KEY, USER_GROUP_MAP_CACHE_KEY
from shield.models import Rule
from django.core.cache import cache

from api_basebone.signals import post_bsm_create, post_bsm_delete

log = logging.getLogger(__name__)


HAS_SHIELD_MODEL = hasattr(settings, 'SHIELD_MODEL')


@receiver(post_bsm_create, sender=Rule, dispatch_uid='clean_rule_cache_by_save')
def clean_rule_cache_by_save(sender, instance: Rule, create, request, old_instance, **kwargs):
    log.debug('clean shield rules by saving')
    if (not create) and ((old_instance.model.pk != instance.model.pk) if HAS_SHIELD_MODEL else (old_instance.model != instance.model)):
        if HAS_SHIELD_MODEL:
            model_name = old_instance.model.name.lower()
            app_name = old_instance.model.app.name
        else:
            app_name, model_name = old_instance.model.split('__', 1)
        cache_key = SHIELD_RULES_DICT_CACHE_KEY.format(app_label=app_name, model_slug=model_name)
        cache.delete(cache_key)

    if HAS_SHIELD_MODEL:
        model_name = instance.model.name.lower()
        app_name = instance.model.app.name
    else:
        app_name, model_name = instance.model.split('__', 1)
    cache_key = SHIELD_RULES_DICT_CACHE_KEY.format(app_label=app_name, model_slug=model_name)
    cache.delete(cache_key)


@receiver(post_bsm_delete, sender=Rule, dispatch_uid='clean_rule_cache_by_delete')
def clean_rule_cache_by_delete(sender, instance: Rule, **kwargs):
    log.debug('clean shield rules by deleting')
    if HAS_SHIELD_MODEL:
        model_name = instance.model.name.lower()
        app_name = instance.model.app.name
    else:
        app_name, model_name = instance.model.split('__', 1)
    cache_key = SHIELD_RULES_DICT_CACHE_KEY.format(app_label=app_name, model_slug=model_name)
    cache.delete(cache_key)


@receiver(m2m_changed, sender=get_user_model().groups.through, dispatch_uid='user_group_changed')
def user_group_changed(sender, instance, model, pk_set, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        cache_key = USER_GROUP_MAP_CACHE_KEY
        cache.delete(cache_key)
