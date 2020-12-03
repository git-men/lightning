
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.conf import settings

from api_basebone.core.widgets import widgets
from lightning.admin import Admin
from lightning.decorators import lightning_admin

User = get_user_model()

@lightning_admin
class UserAdmin(Admin):

    display = ['username', 'is_active', 'is_superuser', 'groups']
    form_fields = [
        'username',
        {'name': 'password', 'widget': widgets.PasswordInput},
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
    ]

    inline_actions = ['edit', 'delete']
    table_actions = [
        'add',
    ]
    class Meta:
        model = User


if hasattr(Group,'_meta'):
    setattr(Group._meta,'verbose_name','角色')
    setattr(Group._meta,'verbose_name_plural','角色')

class UserGMeta:
    title_field = getattr(settings, 'USER_MODEL_TITLE_FIELD', 'username')
    exclude_fields = ['password']
    field_form_config = {'password': {'required': False}}

setattr(User, 'GMeta', UserGMeta)

@lightning_admin
class GroupAdmin(Admin):
    display = ['name']
    modal_form = False
    form_fields = [
        'name',
        {
            'name': 'permissions',
            'widget': 'PermissionSelect',
            'params': {'titlefield': 'name', 'listStyle': {'width': 300, 'height': 400}},
        },
    ]

    inline_actions = ['edit', 'delete']

    class Meta:
        model = Group


@lightning_admin
class PermissionAdmin(Admin):
    filter = ['name', 'content_type', 'codename']
    display = ['name', 'display_name', 'content_type', 'content_type.app_label', 'codename']
    form_fields = ['name', 'codename']

    class Meta:
        model = Permission
