from functools import wraps
from api_basebone.export.specs import FieldType

BSM_BATCH_ACTION = 'bsm_action_map'
BSM_CLIENT_BATCH_ACTION = 'bsm_client_action_map'
BSM_ADMIN_COMPUTED_FIELDS_MAP = 'bsm_admin_computed_fields_map'


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


def basebone_admin_property(model, display_name, field_type=None):
    """
    管理端计算属性字段，管理端配置时，输出对应的数据

    FIXME: 暂时在 bsm admin 类中使用

    Params:
        display str 字段的可读名称
        field_type str 字段的类型
    """
    # 如果没有指定字段类型，则默认是字符串
    if not field_type:
        field_type = FieldType.STRING

    def middle(func):
        @wraps(func)
        def wrapper(self, instance):
            return func(self, instance)

        name = func.__name__
        computed_property = getattr(model, BSM_ADMIN_COMPUTED_FIELDS_MAP, None)
        if not isinstance(computed_property, dict):
            setattr(model, BSM_ADMIN_COMPUTED_FIELDS_MAP, {})

        if name not in model.bsm_admin_computed_fields_map:
            model.bsm_admin_computed_fields_map[name] = {
                'display_name': display_name,
                'field_type': field_type,
            }
        return wrapper

    return middle
