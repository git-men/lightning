import imaplib
from collections import OrderedDict

from django.db import models

from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from .utils import meta


class RecursiveSerializer(serializers.Serializer):
    """递归序列化类，目标是为了形成树形数据结构"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class BaseModelSerializerMixin:
    """通用的序列化类的抽象"""

    class Meta:
        fields = '__all__'

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        # 获取反向字段 related_name 和 name 的映射
        model, reverse_field_map = self.Meta.model, {}
        reverse_fields = meta.get_reverse_fields(model)

        if reverse_fields:
            for item in reverse_fields:
                related_name = meta.get_relation_field_related_name(
                    item.related_model, item.remote_field.name
                )
                if related_name:
                    reverse_field_map[related_name[0]] = item.name

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            elif isinstance(attribute, models.Manager):
                data = attribute.all()

                # 检测字段是否是反向字段的 related_name, 如果是，转换为反向字段的名称
                field_name = reverse_field_map[field.field_name] if field.field_name in reverse_field_map else field.field_name 
                ret[field_name] = field.to_representation(data)
            else:
                ret[field.field_name] = field.to_representation(attribute)
        return ret


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

        if meta.check_field_is_reverse(field):
            many = False if field.one_to_one else True
            serializer_class = create_serializer_class(field.related_model)
            related_name = meta.get_relation_field_related_name(
                field.related_model, field.remote_field.name
            )
            if related_name:
                attrs[related_name[0]] = serializer_class(many=many)
        else:
            serializer_class = create_nested_serializer_class(field.related_model, value)
            many = True if field.many_to_many else False
            attrs[key] = serializer_class(many=many)
    return create_serializer_class(
        model, exclude_fields=None, tree_structure=tree_structure, **attrs
    )
