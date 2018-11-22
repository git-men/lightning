from functools import wraps

BSM_BATCH_ACTION = 'bsm_action_map'

BSM_CLIENT_BATCH_ACTION = 'bsm_client_action_map'


def action(model, name):
    """
    管理端批量操作的连接器

    可以把动作连接到对应的模型中去
    """
    def middle(func):
        @wraps(func)
        def wrapper(request, queryset):
            return func(request, queryset)
        wrapper.short_description = name

        bsm_action_map = getattr(model, BSM_BATCH_ACTION, None)
        if bsm_action_map is None:
            setattr(model, BSM_BATCH_ACTION, {})

        action_map = getattr(model, BSM_BATCH_ACTION)
        action_map[func.__name__.lower()] = wrapper
        return wrapper
    return middle


def client_action(model, name):
    """客户端批量操作装饰器"""

    def middle(func):
        @wraps(func)
        def wrapper(request, queryset):
            return func(request, queryset)
        wrapper.short_description = name

        bsm_action_map = getattr(model, BSM_CLIENT_BATCH_ACTION, None)
        if bsm_action_map is None:
            setattr(model, BSM_CLIENT_BATCH_ACTION, {})

        action_map = getattr(model, BSM_CLIENT_BATCH_ACTION)
        action_map[func.__name__.lower()] = wrapper
        return wrapper
    return middle
