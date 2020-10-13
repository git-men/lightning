"""
按照这个实现，有一个问题：
优化师能看自己发起的数据，设计师能看自己设计的数据。
分别对优化师和设计师设置了规则，并赋予了两个角色的can view权限。
有一天，管理员将设计师的can view权限去除，但规则没去除，
那么如果一个用户，既是优化师又是设计师，就不止能看自己发起的数据，还能看自己设计的数据。
TODO 一个方案是，将rule按角色分组后，还要判断其角色有没有can view权限，再决定要不要OR进来。
"""
import logging
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q

from api_basebone.restful.manage.views import QuerySetMixin
from .models import Rule
log = logging.getLogger(__name__)

SHIELD_RULES_DICT_CACHE_KEY = 'shield_rules_dict:{app_label}.{model_slug}'
USER_GROUP_MAP_CACHE_KEY = 'user_group_map'


def get_role_config_with_group(app_label, model_slug):
    if hasattr(settings, 'SHIELD_RULES'):
        return settings.SHIELD_RULES.get(f'{app_label}__{model_slug}', [])

    cache_key = SHIELD_RULES_DICT_CACHE_KEY.format(app_label=app_label, model_slug=model_slug)
    record = cache.get(cache_key, None)
    if record:
        return record
    model_q = Q(model__app__name=app_label, model__name__iexact=model_slug) if hasattr(settings, 'SHIELD_MODEL') else Q(model=f'{app_label}__{model_slug}')
    rules = Rule.objects.filter(model_q).prefetch_related('condition_set', 'groups').all()
    result = [r.get_rule() for r in rules]
    cache.set(cache_key, result, 600)
    return result


def get_user_group_map():
    cache_key = USER_GROUP_MAP_CACHE_KEY
    record = cache.get(cache_key, None)
    if record:
        return record
    result = defaultdict(set)
    groups = get_user_model().groups
    for user, group_name in groups.through.objects.values_list(groups.field.m2m_field_name(), 'group__name'):
        result[user].add(group_name)
    cache.set(cache_key, result, 600)
    return result


none = {'field': 'pk', 'operator': 'in', 'value': []}  # trick，可以避免django发起数据库查询，返回空列表，效果相当于.none()


def basebone_get_model_role_config(self):
    filters = [none]  # 默认返回空列表
    rules = get_role_config_with_group(self.app_label, self.model_slug)
    user_group_map = get_user_group_map()
    user_groups = user_group_map.get(self.request.user.id, set())
    if not rules:  # 开放所有人都能访问的模型
        filters = []
    elif user_groups:  # 无角色的用户不允许访问有rule的模型
        group = defaultdict(list)
        for r in rules:
            for g in user_groups & r['groups'] if r['groups'] else user_groups:
                group[g] += r['conditions']
        if group:  # 无匹配角色则返回空列表
            filters = []
            if all(group.values()):  # 其中任一角色能够看到全部数据，都直接返回全部，否则将各角色的查询条件OR起来
                filters.append({
                    'operator': 'OR',
                    'children': [{
                        'operator': 'AND',
                        'children': cs,
                    } for cs in group.values()]
                })
    return {
        'use_admin_filter_by_login_user': False,
        'distinct': bool(filters) and filters != [none],
        'filters': filters,
    }


QuerySetMixin.basebone_get_model_role_config = basebone_get_model_role_config
