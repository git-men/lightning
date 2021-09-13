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


class PanelMeta(type):
    def __init__(cls, name, bases, attrs):
        meta = attrs.pop('Meta', None)
        super().__init__(name, bases, attrs)
        cls._meta = meta


class Panel(metaclass=PanelMeta):
    @classmethod
    def to_dict(cls):
        meta = cls._meta
        result = {attr: getattr(meta, attr) for attr in [
            'permission_code', 'title', 'key', 'help_text',
        ] if hasattr(meta, attr)}
        result['fields'] = [{'name': k, **v.to_dict()} for k, v in cls.__dict__.items() if isinstance(v, Field)]

        return result
