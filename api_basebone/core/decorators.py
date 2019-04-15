from functools import wraps

BSM_BATCH_ACTION = 'bsm_action_map'
BSM_CLIENT_BATCH_ACTION = 'bsm_client_action_map'


def action(model, verbose_name='', manage=True):
    """
    管理端批量操作的连接器

    可以把动作连接到对应的模型中去

    Params:
        model class 模型类
        verbose_name str 函数描述
        manage bool 是否是针对管理端，客户端写 False
    """
    def middle(func):

        @wraps(func)
        def wrapper(request, queryset):
            return func(request, queryset)

        if verbose_name:
            wrapper.short_description = verbose_name

        end_slug = BSM_BATCH_ACTION if manage else BSM_CLIENT_BATCH_ACTION
        bsm_action_map = getattr(model, end_slug, None)
        if bsm_action_map is None:
            setattr(model, end_slug, {})

        action_map = getattr(model, end_slug)
        action_map[func.__name__.lower()] = wrapper
        return wrapper
    return middle
