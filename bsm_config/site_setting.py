from django.conf import settings


def default_get_field(field):
    f = {
        "displayName": field.get('displayName', field['name']),
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
    return f


class Field:
    type = None
    get_field = staticmethod(default_get_field)

    def __init__(self, **kwargs):
        self.inner_dict = kwargs

    def to_dict(self):
        return {**self.inner_dict, 'type': self.type}


class BoolField(Field):
    type = 'bool'


class StringField(Field):
    type = 'string'


class TextField(Field):
    type = 'text'


class DecimalField(Field):
    type = 'decimal'


class IntegerField(Field):
    type = 'integer'


class FieldDict(dict):
    def __init__(self, name, field_type):
        super().__init__(name=name, **field_type.to_dict())
        self.field_type = field_type

    def get_field(self):
        return self.field_type.get_field(self)


def default_get_schemas(default_schemas):
    return default_schemas


class Panel:
    get_schemas = staticmethod(default_get_schemas)

    @classmethod
    def to_dict(cls, meta):
        meta['fields'] = [FieldDict(k, v) for k, v in cls.__dict__.items() if isinstance(v, Field)]
        return meta


class PanelDict(dict):
    def __init__(self, panel, **kwargs):
        super().__init__(**panel.to_dict(kwargs))
        self.panel = panel

    def get_schemas(self, default_schemas):
        return self.panel.get_schemas(default_schemas)


class PanelMeta:
    kwargs = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, panel: Panel):
        settings.WEBSITE_CONFIG.append(PanelDict(panel, **self.kwargs))


def register_panel(**kwargs):
    return PanelMeta(**kwargs)
