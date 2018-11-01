from functools import wraps

BSM_BATCH_ACTION = 'bsm_action_map'


def action(model, name):
    """
    批量操作的连接器

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
