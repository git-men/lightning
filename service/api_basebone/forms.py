from rest_framework import serializers


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta"""

    attrs = {
        'model': model,
        'fields': '__all__'
    }
    if exclude_fields is not None:
        attrs['exclude'] = exclude_fields

    return type('Meta', (object, ), attrs)


def create_form_class(model, exclude_fields=None, **kwargs):
    """构建序列化类"""

    attrs = {
        'Meta': create_meta_class(model, exclude_fields=None)
    }
    attrs.update(kwargs)

    class_name = f'{model}ModelSerializer'
    return type(
        class_name,
        (serializers.ModelSerializer, ),
        attrs
    )
