from django.conf import settings
from api_basebone.export.specs import FieldType


class UserGMeta:
    title_field = getattr(settings, 'USER_MODEL_TITLE_FIELD', 'fullname')
    computed_fields = [
        {'name': 'fullname', 'type': FieldType.STRING, 'display_name': '名字'}
    ]
    exclude_fields = ['password']
    field_form_config = {'password': {'required': False}}

