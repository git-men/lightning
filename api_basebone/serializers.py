import imaplib
from collections import OrderedDict

from rest_framework import serializers


class RecursiveSerializer(serializers.Serializer):
    """递归序列化类，目标是为了形成树形数据结构"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class BaseModelSerializerMixin:
    """通用的序列化类的抽象"""

    class Meta:
        fields = '__all__'


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta

    Params:
        exclude_fields list 排除的字段
    """

    attrs = {
        'model': model,
        'fields': '__all__'
    }
    if exclude_fields is not None:
        attrs['exclude'] = exclude_fields

    return type('Meta', (object, ), attrs)


def create_serializer_class(model, exclude_fields=None, tree_structure=None, **kwargs):
    """构建序列化类

    Params:
        tree_structure 元组 admin 中做对应配置
    """

    attrs = {
        'Meta': create_meta_class(model, exclude_fields=None)
    }
    attrs.update(kwargs)

    # 动态构建树形结构的字段
    if tree_structure:
        attrs[tree_structure[1]] = RecursiveSerializer(many=True)

    class_name = f'{model}ModelSerializer'
    return type(
        class_name,
        (BaseModelSerializerMixin, serializers.ModelSerializer, ),
        attrs
    )


def range_expand_fields(fields):
    assert isinstance(fields, list), '扩展字段应该是一个列表'

    result = {}
    for item in fields:
        if '.' not in item:
            if item not in result:
                result[item] = [item]
        else:
            name = item.split('.', maxsplit=1)[0]
            if name not in result:
                result[name] = [item]
            else:
                result[name].append(item)

    for key, value in result.items():
        result[key] = sorted(value, key=len, reverse=True)[0].split('.')
    return result


def dg_attrs(index, model, field_dict, stop):
    if index == 0:
        model = model
    else:
        field_name = field_dict[index]['field_name']
        field = model._meta.get_field(field_name)

        field_dict[index]['field'] = field
        field_dict[index]['model'] = field.related_model
        field_dict[index]['many'] = field.many_to_many
        model = field.related_model

    index += 1
    if index < stop:
        dg_attrs(index, model, field_dict, stop)


def create_nested_serializer_class(model, field_list):
    """构建嵌套序列化类

    此方法仅仅为 multiple_create_serializer_class 方法服务
    """
    field_length = len(field_list)
    if field_length == 1:
        return create_serializer_class(model)

    field_dict = OrderedDict()
    for index, item in enumerate(field_list):
        field_dict[index] = {
            'field_name': item,
            'model': model,
        }

    dg_attrs(0, model, field_dict, field_length)

    for key, value in reversed(field_dict.items()):
        if key == (field_length - 1):
            value['serializer'] = create_serializer_class(value['model'])
        else:
            prev_value = field_dict[key + 1]
            many = True if prev_value['many'] else False
            serializer_class = prev_value['serializer']

            attrs = {
                prev_value['field_name']: serializer_class(many=many)
            }
            value['serializer'] = create_serializer_class(value['model'], **attrs)
    return field_dict[0]['serializer']


def multiple_create_serializer_class(model, expand_fields, tree_structure=None):
    """多重创建序列化类"""

    expand_dict = range_expand_fields(expand_fields)
    attrs = {}

    for key, value in expand_dict.items():
        field = model._meta.get_field(key)
        serializer_class = create_nested_serializer_class(field.related_model, value)

        many = True if field.many_to_many else False
        attrs[key] = serializer_class(many=many)

    return create_serializer_class(
        model, exclude_fields=None, tree_structure=tree_structure, **attrs
    )
