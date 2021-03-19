from collections import Mapping, OrderedDict

from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField
from rest_framework import fields, serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject

from api_basebone.const.field_map import (
    ComputedFieldTypeSerializerMap,
    ExportFieldTypeSerializerMap,
)
from api_basebone.core import drf_field, gmeta
from api_basebone.core.decorators import BSM_ADMIN_COMPUTED_FIELDS_MAP
from api_basebone.core.fields import JSONField
from jsonfield import JSONField as OriginJSONField
from rest_framework.fields import JSONField as DrfJSONField
from api_basebone.drf.fields import CharIntegerField
from api_basebone.export.fields import get_attr_in_gmeta_class
from api_basebone.utils import meta, module
from api_basebone.utils.gmeta import get_gmeta_config_by_key
from api_basebone.utils.module import import_class_from_string

from .const import MANAGE_END_SLUG

# 导出文件的动作
EXPORT_FILE_ACTION = 'export_file'


class ModelSerializer(serializers.ModelSerializer):

    pass


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

            check_for_none = (
                attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            )
            if check_for_none is None:
                ret[field.field_name] = None
            elif isinstance(attribute, models.Manager):
                data = attribute.all()

                # 检测字段是否是反向字段的 related_name, 如果是，转换为反向字段的名称
                field_name = (
                    reverse_field_map[field.field_name]
                    if field.field_name in reverse_field_map
                    else field.field_name
                )
                ret[field_name] = field.to_representation(data)
            else:
                ret[field.field_name] = field.to_representation(attribute)

        # 这了处理 admin 中计算属性字段的业务
        if self.basebone_end_slug == MANAGE_END_SLUG:
            admin_computed_fields = getattr(
                self.basebone_model, BSM_ADMIN_COMPUTED_FIELDS_MAP, {}
            )
            if not admin_computed_fields:
                return ret
            admin_class = meta.get_bsm_model_admin(self.basebone_model)
            if not admin_class:
                return ret

            admin_instance = admin_class()
            for name, field_value in admin_computed_fields.items():
                field_type = field_value['field_type']
                computed_func = getattr(admin_instance, name, None)
                if not computed_func:
                    continue
                value = computed_func(instance)
                serializer_class = ComputedFieldTypeSerializerMap[field_type]
                # 如果是导出，则使用导出的字段序列化类
                if (
                    self.action == EXPORT_FILE_ACTION
                    and field_type in ExportFieldTypeSerializerMap
                ):
                    serializer_class = ExportFieldTypeSerializerMap[field_type]
                ret[name] = serializer_class(read_only=True).to_representation(value)
        return ret


class CustomModelSerializer(serializers.ModelSerializer):
    """由于BigInteger类型的数据到了前端，JS丢失了精度，所以在接口返回的时候就直接转成字符串
    """

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.BigIntegerField] = CharIntegerField
    serializer_field_mapping[models.BigAutoField] = CharIntegerField


def create_meta_class(
    model, exclude_fields=None, extra_fields=None, action=None, display_fields=None, allow_one_to_one=False, **kwargs
):
    """构建序列化类的 Meta

    Params:
        exclude_fields list 排除的字段
    """

    attrs = {'model': model}

    exclude_field_list = get_model_exclude_fields(model, exclude_fields)
    if action in ['list', 'set']:
        flat_fields = [
            f.name
            for f in model._meta.get_fields()
            if f.concrete
            and not (
                f.is_relation
                and (not isinstance(f, ForeignKey) or isinstance(f, OneToOneField))
            )
        ]
    else:
        flat_fields = [
            f.name
            for f in model._meta.get_fields()
            if f.concrete and (not isinstance(f, OneToOneField) or allow_one_to_one)
        ]

    if display_fields is not None and '*' not in display_fields:
        flat_fields = list(set(flat_fields) & set(display_fields))

    if extra_fields:
        flat_fields += extra_fields

    if exclude_field_list:
        attrs['fields'] = list(set(flat_fields).difference(set(exclude_field_list)))
    else:
        attrs['fields'] = flat_fields
    return type('Meta', (object,), attrs)


def create_serializer_class(
    model,
    exclude_fields=None,
    tree_structure=None,
    action=None,
    end_slug=None,
    attrs=None,
    display_fields=None,
    allow_one_to_one=False,
):
    """构建序列化类

    Params:
        tree_structure 元组 admin 中做对应配置
    """
    if attrs is None:
        attrs = {}

    def __init__(self, *args, **kwargs):
        """
        重置导出的字段映射，因为类似 BooleanField 字段，显示为中文会比较友好
        """
        self.serializer_field_mapping[JSONField] = drf_field.JSONField
        self.serializer_field_mapping[OriginJSONField] = DrfJSONField
        if self.action == 'export_file':
            self.serializer_field_mapping[
                models.BooleanField
            ] = drf_field.ExportBooleanField
            self.serializer_field_mapping[
                models.DateTimeField
            ] = drf_field.ExportDateTimeField
            self.serializer_choice_field = drf_field.ExportChoiceField
        else:
            # 恢复为原来的字段类型映射，因为上面改了类的变量属性值
            self.serializer_field_mapping[models.BooleanField] = fields.BooleanField
            self.serializer_field_mapping[models.DateTimeField] = fields.DateTimeField
            self.serializer_choice_field = fields.ChoiceField

        super(CustomModelSerializer, self).__init__(*args, **kwargs)

    extra_fields = list(attrs.keys())
    new_attr = {}
    # 动态构建树形结构的字段
    if tree_structure:
        extra_fields.append(tree_structure[1])
        new_attr[tree_structure[1]] = RecursiveSerializer(many=True)

    # 构建计算属性字段
    computed_fields = get_gmeta_config_by_key(model, gmeta.GMETA_COMPUTED_FIELDS)
    if computed_fields:
        extra_fields += [f['name'] for f in computed_fields]
        for field in computed_fields:
            name = field['name']
            field_type = field['type']

            # 如果是导出，则使用导出的字段序列化类
            if (
                action == EXPORT_FILE_ACTION
                and field_type in ExportFieldTypeSerializerMap
            ):
                new_attr[name] = ExportFieldTypeSerializerMap[field_type](read_only=True)
            else:
                new_attr[name] = ComputedFieldTypeSerializerMap[field_type](
                    read_only=True
                )

    # 构建annotate算属性字段
    annotated_fields = get_attr_in_gmeta_class(model, gmeta.GMETA_ANNOTATED_FIELDS, {})
    if annotated_fields:
        extra_fields += annotated_fields.keys()
        for name, field in annotated_fields.items():
            new_attr[name] = ComputedFieldTypeSerializerMap[field['type']](read_only=True)

    class_name = f'{model.__name__}ModelSerializer'
    return type(
        class_name,
        (BaseModelSerializerMixin, CustomModelSerializer),
        {
            'Meta': create_meta_class(
                model,
                exclude_fields=exclude_fields,
                extra_fields=extra_fields,
                display_fields=display_fields,
                action=action,
                allow_one_to_one=allow_one_to_one,
            ),
            'action': action,
            'basebone_model': model,
            'basebone_end_slug': end_slug,
            '__init__': __init__,
            **new_attr,
            **attrs,
        },
    )


def get_field(model, field_name):
    """
    获取字段

    Params:
        field_name str 字段名或者反向字段的 related_name

    Returns:
        field 指定 model 的字段
    """
    valid_fields = {item.name: item for item in model._meta.get_fields()}
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
        if (
            key in dct
            and isinstance(dct[key], dict)
            and isinstance(merge_dct[key], Mapping)
        ):
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


def nested_display_fields(model, super_display_fields, key):
    if not super_display_fields:
        return None

    reverse_fields = meta.get_reverse_fields(model)

    reverse_field_map = {}
    if reverse_fields:
        for item in reverse_fields:
            related_name = meta.get_relation_field_related_name(
                item.related_model, item.remote_field.name
            )
            if related_name:
                reverse_field_map[related_name[0]] = item.name
    if key in reverse_field_map:
        key = reverse_field_map[key]
    return ['.'.join(d.split('.')[1:]) for d in super_display_fields if d.startswith(key+'.')]


def create_nested_serializer_class(
    model, field_list, exclude_fields=None, action=None, end_slug=None, display_fields=None, **kwargs
):
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
                field.related_model,
                exclude_fields=exclude_fields,
                action=action,
                end_slug=end_slug,
                display_fields=nested_display_fields(model, display_fields, key),
            )(many=many)
        else:
            attrs[key] = create_nested_serializer_class(
                field.related_model,
                value,
                exclude_fields=exclude_fields,
                action=action,
                end_slug=end_slug,
                display_fields=nested_display_fields(model, display_fields, key),
            )(many=many)
    return create_serializer_class(
        model,
        exclude_fields=exclude_fields,
        action=action,
        end_slug=end_slug,
        attrs=attrs,
        display_fields=display_fields,
        allow_one_to_one=True,
    )


def display_fields_to_expand_fields(display_fields):
    return [d.rsplit('.', 1)[0] for d in display_fields if '.' in d]


def multiple_create_serializer_class(
    model,
    expand_fields=None,
    tree_structure=None,
    exclude_fields=None,
    action=None,
    end_slug=None,
    display_fields=None,
):
    """多重创建序列化类"""
    attrs = {}

    if expand_fields is None:
        if display_fields is not None:
            expand_fields = display_fields_to_expand_fields(display_fields)
        else:
            expand_fields = []
    expand_dict = sort_expand_fields(expand_fields)
    for key, value in expand_dict.items():
        field = get_field(model, key)
        # 如果是反向字段，则使用另外一种方式
        many = field.many_to_many
        if meta.check_field_is_reverse(field):
            many = False if field.one_to_one else True

        attrs[key] = create_nested_serializer_class(
            field.related_model,
            value,
            exclude_fields=exclude_fields,
            action=action,
            end_slug=end_slug,
            display_fields=nested_display_fields(model, display_fields, key)
        )(many=many)
    return create_serializer_class(
        model,
        exclude_fields=exclude_fields,
        tree_structure=tree_structure,
        action=action,
        end_slug=end_slug,
        display_fields=display_fields,
        attrs=attrs,
    )


def get_export_serializer_class(
    model, serialier_class, custom_serializer_class=None, version=None
):
    """获取导出的序列化类

    如果用户有自定义的导出类，则合并序列化类和用户自定义的，如果没有，则使用默认的序列化类

    Params:
        model class 模型类
        serialier_class class 序列化类

    Returns:
        class 表单类
    """
    custom_export_mixin = None
    class_name = '{}ExportSerializer'.format(model.__name__)
    if version:
        class_name = f'{class_name}{version}'

    if custom_serializer_class is None:
        export_module = module.get_admin_module(
            model._meta.app_config.name, module.BSM_EXPORT
        )
        custom_export_mixin = getattr(export_module, class_name, None)
    else:
        _, class_name = custom_serializer_class.rsplit('.', 1)
        custom_export_mixin = import_class_from_string(custom_serializer_class)

    if custom_export_mixin is None:
        return serialier_class

    class_name = f'Model{class_name}'

    reset_serialzier_class = custom_export_mixin.get_serializer_class(serialier_class)
    return type(class_name, (reset_serialzier_class,), {})
