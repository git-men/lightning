from bsm_config.models import Setting

def get_field_value(field):
    type_mapping = {'string': field.value, 'bool': field.value == str(True) }
    return type_mapping.get(field.type, field.value)

def get_settins():
    data = Setting.objects.filter(is_admin=False).all()
    settings = {}
    for setting in data:
        settings.update({
            setting.key: get_field_value(setting)
        })
    return settings