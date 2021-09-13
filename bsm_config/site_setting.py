from django.conf import settings


class Field:
    type = None

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


class Panel:
    @classmethod
    def to_dict(cls, meta):
        meta['fields'] = [{'name': k, **v.to_dict()} for k, v in cls.__dict__.items() if isinstance(v, Field)]
        return meta


class PanelMeta:
    kwargs = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, panel: Panel):
        settings.WEBSITE_CONFIG.append(panel.to_dict(self.kwargs))


def register_panel(**kwargs):
    return PanelMeta(**kwargs)
