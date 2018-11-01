"""
动作

种类的动作可以应对各种场合，即约定型的操作

例如批量动作可以批量删除，批量更新，批量创建，甚至是批量中可以支持多种动作的混合
"""

import importlib
from rest_framework import serializers
from api_basebone.core import exceptions
from api_basebone.core.decorators import BSM_BATCH_ACTION


def delete(request, queryset):
    """默认的删除处理器"""
    queryset.delete()


delete.short_description = '删除'


default_action_map = {
    'delete': delete
}


def get_model_action(model):
    """获取模型的批量操作动作"""
    bsm_batch_actions = {}
    bsm_batch_actions.update(default_action_map)

    try:
        importlib.import_module(f'{model._meta.app_label}.bsm.actions')
        model_actions = getattr(model, BSM_BATCH_ACTION, None)
        if model_actions:
            bsm_batch_actions.update(model_actions)
    except Exception:
        pass

    return bsm_batch_actions


class BatchActionForm(serializers.Serializer):
    """批量操作的验证表单"""

    action = serializers.CharField(max_length=20)
    data = serializers.ListField(min_length=1)

    def get_model_action_map(self):
        """获取模型的动作映射"""
        view = self.context['view']
        try:
            importlib.import_module(f'{view.app_label}.bsm.actions')
            return getattr(view.model, BSM_BATCH_ACTION, None)
        except Exception:
            return

    def validate_action(self, value):
        """校验 action"""
        bsm_batch_actions = {}
        bsm_batch_actions.update(default_action_map)
        model_action = self.get_model_action_map()
        if model_action:
            bsm_batch_actions.update(model_action)
        if value not in bsm_batch_actions:
            raise exceptions.BusinessException(
                error_code=exceptions.PARAMETER_FORMAT_ERROR,
                error_data='传入的 action: {} 不支持'.format(value)
            )
        self.bsm_batch_action = bsm_batch_actions[value]
        return value

    def validate_data(self, value):
        model = self.context.get('view').model
        filter_params = {'id__in': value}

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
        return self.bsm_batch_action(request, self.bsm_batch_queryset)
