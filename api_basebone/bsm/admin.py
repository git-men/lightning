from api_basebone.core.admin import BSMAdmin, register
from api_basebone.models import AdminLog


@register
class UserAdmin(BSMAdmin):

    display = [
        'action_time',
        'user.username',
        'action',
        'app_label',
        'model_slug',
        'object_id',
        'params',
    ]

    class Meta:
        model = AdminLog
