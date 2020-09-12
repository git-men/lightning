from django.db.models.fields import Field


class Options:
    """
    为了满足api_basebone.export.fields.get_model_field_config
    可能需要添加其他方法
    """
    def __init__(self, fields, model):
        self.fields = fields
        self.model = model
        self.attach_field_attr()

    def attach_field_attr(self):
        for field in self.fields:
            field.concrete = True
            field.model = self.model

    def get_fields(self):
        return self.fields


class ModelBase(type):
    """Metaclass for JsonObjectModel models."""

    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        fields = []
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key
                fields.append(value)
        _meta = Options(fields, cls)
        _meta.model_name = name.lower()
        _meta.verbose_name = getattr(attrs.pop('Meta'), 'verbose_name', _meta.model_name) if 'Meta' in attrs else _meta.model_name
        _meta.app_label = ''
        new_attrs['_meta'] = _meta
        new_attrs['__module__'] = attrs['__module__']
        model = super(ModelBase, cls).__new__(cls, name, bases, new_attrs)
        return model


class ObjectModel(metaclass=ModelBase):
    """
    用来描述json对象结构的模型
    为了满足api_basebone.export.fields.get_model_field_config
    """

    class Meta:
        abstract = True
