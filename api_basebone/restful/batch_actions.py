"""
动作

种类的动作可以应对各种场合，即约定型的操作

例如批量动作可以批量删除，批量更新，批量创建，甚至是批量中可以支持多种动作的混合
"""

import importlib
from rest_framework import serializers
from api_basebone.core import exceptions
from api_basebone.core.decorators import BSM_BATCH_ACTION, BSM_CLIENT_BATCH_ACTION
from api_basebone.utils import module
from api_basebone.restful.const import CLIENT_END_SLUG, MANAGE_END_SLUG


def delete(request, queryset):
    """默认的删除处理器"""
    queryset.delete()


delete.short_description = '删除'


default_action_map = {
    'delete': delete
}


def get_model_batch_actions(model, end=MANAGE_END_SLUG):
    """获取模型的批量操作动作的映射

    默认的动作和用户自定义的动作的结合，用户自定义的动作可以覆盖默认的动作
    """
    batch_actions = {}
    batch_actions.update(default_action_map)

    action_module = module.get_admin_module(model._meta.app_config.name, module.BSM_BATCH_ACTION)
    if action_module:
        end_map_name = BSM_BATCH_ACTION if end == MANAGE_END_SLUG else BSM_CLIENT_BATCH_ACTION
        model_actions = getattr(model, BSM_BATCH_ACTION, None)
        if model_actions:
            batch_actions.update(model_actions)
    return batch_actions


class BatchActionForm(serializers.Serializer):
    """批量操作的验证表单"""

    action = serializers.CharField(max_length=20)
    data = serializers.ListField(min_length=1)

    def validate_action(self, value):
        """
        - 校验 action
        - 记录当前批量动作
        """
        view = self.context['view']
        actions = get_model_batch_actions(view.model, end=view.end_slug)

        if value not in actions:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='传入的 action: {} 不支持'.format(value)
            )
        self.bsm_batch_action = actions[value]
        return value

    def validate_data(self, value):
        """
        - 校验 data
        - 记录当前批量的数据
        """
        model = self.context.get('view').model
        filter_params = {f'{model._meta.pk.name}__in': value}

        queryset = model.objects.filter(**filter_params)
        if len(value) != queryset.count():
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_BUSINESS_ERROR,
                error_message='列表中包含不合法 id 的数据'
            )
        self.bsm_batch_queryset = queryset
        return value

    def handle(self):
        request = self.context['request']
        try:
            return self.bsm_batch_action(request, self.bsm_batch_queryset)
        except Exception as e:
            raise exceptions.BusinessException(
                error_code=exceptions.BATCH_ACTION_HAND_ERROR,
                error_data=str(e)
            )
