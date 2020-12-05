from django.apps import apps
from bsm_config.settings import site_setting, WEBSITE_CONFIG


def get_settins():
    view_keys = []
    if WEBSITE_CONFIG:
        for section in WEBSITE_CONFIG:
            for field in section['fields']:
                if field.get('public',False):
                    view_keys.append(field['name'])
    
    setting_dict = site_setting.get_values(view_keys)

    return setting_dict

def get_setting_config():
    config = []
    if WEBSITE_CONFIG:
        for section in WEBSITE_CONFIG:
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
                    "type": field.get('type','string'),
                    "required": field.get('required',False),
                }
                if 'choices' in field:
                    f['choices'] = field['choices']
                if 'default' in field:
                    f['default'] = field['default']
                if 'validators' in field:
                    f['validators'] = field['validators']
                fields.append(f)
                formField = {'name': field.get('name',''),}
                if 'widget' in field:
                    formField['widget'] = field['widget']
                if 'show' in field:
                    formField['show'] = field['show'] 
                if 'options' in field:
                    formField['options'] = field['options']
                formFields.append(formField)
                value = site_setting[field['name']] 

                # 在site_setting里已经处理好default这个逻辑了，所以注释了
                #if value==None:
                #    value = field.get('default',None)

                if f['type'] in ('mref',):
                    f['ref'] = field['ref']
                    if not value:
                        value = []
                    if value:
                        app, model = f['ref'].split('__')
                        Model = apps.get_app_config(app).get_model(model.capitalize())
                        value = Model.objects.filter(pk__in=value).values()
                values[field['name']] = value

            setting = {
                "title": section.get('title',None), "model": model,
                "schemas": {model:{"fields":fields}},
                'admins': {model: {"formFields": formFields}},
                "values": values,
                "help_text": section.get('help_text',''),
                "permission_code": f'bsm_config.{section.get("permission_code","")}'
            }
            config.append(setting)

    return config
