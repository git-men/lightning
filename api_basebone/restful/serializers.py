from collections import OrderedDict, Mapping

from django.db import models

from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework import fields

from api_basebone.core import gmeta
from api_basebone.utils import meta
from api_basebone.utils.gmeta import get_gmeta_config_by_key

from api_basebone.export.specs import FieldType


FieldTypeSerializerMap = {
    FieldType.STRING: fields.CharField,
    FieldType.INTEGER: fields.IntegerField,
    FieldType.BOOL: fields.BooleanField,
    FieldType.TEXT: fields.CharField,
    FieldType.RICHTEXT: fields.CharField,
    FieldType.FLOAT: fields.FloatField,
    FieldType.DECIMAL: fields.DecimalField,
    FieldType.IMAGE: fields.CharField,
    FieldType.DATE: fields.DateField,
    FieldType.TIME: fields.TimeField,
    FieldType.DATETIME: fields.DateTimeField
}


def get_model_exclude_fields(model, exclude_fields):
    """获取模型序列化输出时的排除字段

    Params:
        model class django 模型类
    """
    field_list = []
    gmeta_class = getattr(model, 'GMeta', None)
    if gmeta_class:
        exclude = getattr(gmeta_class, gmeta.GMETA_SERIALIZER_EXCLUDE_FIELDS, None)
        if exclude and isinstance(exclude, (list, tuple)):
            fields = [item.name for item in model._meta.get_fields()]
            field_list = [item for item in exclude if item in fields]
    key = f'{model._meta.app_label}__{model._meta.model_name}'
    if isinstance(exclude_fields, dict) and exclude_fields:
        if key in exclude_fields and isinstance(exclude_fields[key], list):
            field_list += exclude_fields[key]
    return field_list


class RecursiveSerializer(serializers.Serializer):
    """递归序列化类，目标是为了形成树形数据结构"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class BaseModelSerializerMixin:
    """通用的序列化类的抽象"""

    class Meta:
        fields = '__all__'

    def _to_representation_from_property(self, model, instance):
        """
        获取模型中 property 装饰器装饰的属性值
        """
        for key in dir(model):
            if key != 'pk' and isinstance(getattr(model, key, None), property):
                ret[key] = getattr(instance, key, None)

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


class CustomModelSerializer(serializers.ModelSerializer):
    """由于BigInteger类型的数据到了前端，JS丢失了精度，所以在接口返回的时候就直接转成字符串
    """
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.BigIntegerField] = fields.CharField
    serializer_field_mapping[models.BigAutoField] = fields.CharField

def create_meta_class(model, exclude_fields=None, **kwargs):
    """构建序列化类的 Meta

    Params:
        exclude_fields list 排除的字段
    """

    attrs = {
        'model': model,
    }

    exclude_field_list = get_model_exclude_fields(model, exclude_fields)
    if exclude_field_list is not None and exclude_field_list:
        attrs['exclude'] = exclude_field_list
    else:
        attrs['fields'] = '__all__'

    return type('Meta', (object, ), attrs)


def create_serializer_class(model, exclude_fields=None, tree_structure=None, **kwargs):
    """构建序列化类

    Params:
        tree_structure 元组 admin 中做对应配置
    """
    attrs = {
        'Meta': create_meta_class(model, exclude_fields=exclude_fields)
    }
    attrs.update(kwargs)

    # 动态构建树形结构的字段
    if tree_structure:
        attrs[tree_structure[1]] = RecursiveSerializer(many=True)

    # 构建计算属性字段
    computed_fields = get_gmeta_config_by_key(model, gmeta.GMETA_COMPUTED_FIELDS)
    if computed_fields:
        for field in computed_fields:
            name = field['name']
            field_type = field['type']
            attrs[name] = FieldTypeSerializerMap[field_type](read_only=True)

    class_name = f'{model.__name__}ModelSerializer'
    return type(
        class_name,
        (BaseModelSerializerMixin, CustomModelSerializer, ),
        attrs
    )


def get_field(model, field_name):
    """
    获取字段

    Params:
        field_name str 字段名或者反向字段的 related_name

    Returns:
        field 指定 model 的字段
    """
    valid_fields = {
        item.name: item for item in model._meta.get_fields()
    }
    if field_name in valid_fields:
        return valid_fields[field_name]

    # 如果没有找到指定的字段，则通过反向字段的 related_name 进行查找
    related_field_map = {}
    for field in meta.get_reverse_fields(model):
        related_name = meta.get_relation_field_related_name(
            field.related_model, field.remote_field.name
        )
        if related_name:
            related_field_map[related_name[0]] = field

    if field_name in related_field_map:
        return related_field_map[field_name]


def dict_merge(dct, merge_dct):
    """递归合并字典

    Params:
        dct dict 源字典
        merge_dict dict 待合并的字典
    """
    for key, value in merge_dct.items():
        if key in dct and isinstance(dct[key], dict) and isinstance(merge_dct[key], Mapping):
            dict_merge(dct[key], merge_dct[key])
        else:
            dct[key] = merge_dct[key]
    return dct


def generate_nest_dict(fields):
    """生成嵌套的字典

    例如：abc.allen.girl 将会处理成

    {
        'abc': {
            'allen': {
                'girl': {}
            }
        }
    }
    """
    tree_dict = {}
    for key in reversed(fields.split('.')):
        tree_dict = {key: tree_dict}
    return tree_dict


def sort_expand_fields(fields):
    """
    整理扩展字段

    Params:
        fields list 扩展字段的列表
    """
    assert isinstance(fields, list), '扩展字段应该是一个列表'
    result = {}

    for item in fields:
        dict_merge(result, generate_nest_dict(item))
    return result


def create_nested_serializer_class(model, field_list, exclude_fields=None, **kwargs):
    """构建嵌套序列化类

    此方法仅仅为 multiple_create_serializer_class 方法服务
    """
    field_nest = field_list

    attrs = {}
    for key, value in field_nest.items():
        field = get_field(model, key)
        many = field.many_to_many
        if meta.check_field_is_reverse(field):
            many = False if field.one_to_one else True

        if not value:
            attrs[key] = create_serializer_class(
                field.related_model, exclude_fields=exclude_fields
            )(many=many)
        else:
            attrs[key] = create_nested_serializer_class(
                field.related_model, value, exclude_fields=exclude_fields
            )(many=many)
    return create_serializer_class(model, exclude_fields=exclude_fields, **attrs)


def multiple_create_serializer_class(model, expand_fields, tree_structure=None, exclude_fields=None):
    """多重创建序列化类"""
    attrs = {}

    expand_dict = sort_expand_fields(expand_fields)
    for key, value in expand_dict.items():
        field = get_field(model, key)
        # 如果是反向字段，则使用另外一种方式
        many = field.many_to_many
        if meta.check_field_is_reverse(field):
            many = False if field.one_to_one else True

        attrs[key] = create_nested_serializer_class(
            field.related_model, value, exclude_fields=exclude_fields
        )(many=many)
    return create_serializer_class(
        model,
        exclude_fields=exclude_fields,
        tree_structure=tree_structure,
        **attrs
    )
