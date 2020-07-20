from django.conf import settings
from bsm_config.models import Setting


def get_settins():
    data = Setting.objects.values('key','value_json')
    data_map_key = {item['key']: item['value_json'].get('value',None) for item in data}
    setting_data = {}
    view_keys = []
    if settings.SETTINGS_CONFIG:
        for section in settings.SETTINGS_CONFIG:
            for field in section['fields']:
                if field.get('public',False):
                    view_keys.append(field['name'])
    
    for key in view_keys:
        if key in data_map_key:
            setting_data.update({
                key: data_map_key[key]
            })

    return setting_data

def get_setting_config():
    config = []
    data = Setting.objects.values('key','value_json')
    data_map_key = {item['key']: item['value_json'].get('value',None) for item in data}
    if settings.SETTINGS_CONFIG:
        for section in settings.SETTINGS_CONFIG:
            values = {}
            fields = []
            formFields = []
            model = section['key']
            group_name = f'{model}_group'
            for field in section['fields']:
                f = {
                    "displayName": field.get('displayName',''),
                    "help": field.get('help',''),
                    "name": field['name'],
                    "type": field.get('type',''),
                    "required": field.get('required',False),
                }
                if 'choices' in field:
                    f['choices'] = field['choices']
                fields.append(f)
                formField = {'name': field.get('name',''),}
                if 'widget' in field:
                    formField['widget'] = field['widget']
                if 'show' in field:
                    formField['show'] = field['show'] 
                if 'options' in field:
                    formField['options'] = field['options']
                formFields.append(formField)
                values[field['name']] = data_map_key[field['name']]

            setting = {
                "title": section.get('title',None), "model": model,
                "schemas": {model:{"fields":fields}},
                'admins': {model: {"formFields": formFields}},
                "values": values
            }
            config.append(setting)

    return config