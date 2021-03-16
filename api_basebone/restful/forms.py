import functools
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework.utils.model_meta import get_field_info
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta

from api_basebone.core import drf_field, gmeta
from api_basebone.core.fields import JSONField
from jsonfield import JSONField as OriginJSONField
from rest_framework.fields import JSONField as DrfJSONField
from api_basebone.restful.const import CLIENT_END_SLUG, MANAGE_END_SLUG
from api_basebone.utils import module
from api_basebone.utils.gmeta import get_gmeta_config_by_key
from werkzeug import Local

rfu_modes = Local()

compare_funcs = {
    '=': lambda a, b: a == b,
    '==': lambda a, b: a == b,
    '===': lambda a, b: a == b,
    '>': lambda a, b: a > b,
    '<': lambda a, b: a < b,
    'in': lambda a, b: a in b,
    'include': lambda a, b: b in a,
}

class BulkCreateListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        result = [self.child.create(attrs) for attrs in validated_data]        
        # self.child.Meta.model.objects.bulk_create(result, ignore_conflicts=False)
        
        return result
    
    def update(self, instance, validated_data):
        """批量更新数据,目前只支持批量级新一个层级的字段，关联字段未支持更新
        """
        print('批量更新数据')
        pk_name = instance.model._meta.pk.name
        origins = dict([(ins.pk, ins) for ins in instance])
        ret = []
        for data in validated_data:
            if data[pk_name] not in origins:
                # 不在查询结果中，可能是无权限修改
                continue
            ins = origins[data[pk_name]]
            ret.append(self.child.update(ins, data))
        return ret

def validate_condition_required(
    data, field=[], condition_field=None, operator=None, value=None
):
    """条件性必填校验，如type字段值为0时，price字段才必填。
    """
    # 首先判断条件是否成立
    if not (condition_field and operator and value and condition_field in data):
        return
    test_value = data[condition_field]
    func = compare_funcs.get(operator, None)
    if not func:
        return
    if not func(test_value, value):
        return  # 不符合条件，不用校验

    # 如果条件成立，则保证required_fields里面的字段都有值
    if not isinstance(field, list):
        field = [field]
    messages = []
    for fd in field:
        if fd in data and data[fd]:
            continue
        messages.append((fd, f'{fd}是必填的'))

    if messages:
        raise serializers.ValidationError(dict(messages))


def validate_condition_compare(operator):
    def _validate_condition_compare(data, field=None, condition_field=None):
        """表单范围的大小比较
        """
        if not (
            field
            and condition_field
            and data.get(field, None)
            and data.get(condition_field, None)
        ):
            return
        test_value = data[field]
        condition_value = data[condition_field]
        if operator == 'lt' and test_value >= condition_value:
            raise serializers.ValidationError(
                {field: f'{field}的值必须小于{condition_field}的值'}
            )

        if operator == 'gt' and test_value <= condition_value:
            raise serializers.ValidationError(
                {field: f'{field}的值必须大于{condition_field}的值'}
            )

    return _validate_condition_compare


CONDICTION_VALIDATORS = {
    'condition_required': validate_condition_required,
    'condition_less': validate_condition_compare('lt'),
    'condition_great': validate_condition_compare('gt'),
}


def get_validate(validators):
    def validate(self, data):
        """ModelSerializer 里的Vaidate方法
        """
        # data = super().validate(data)
        for validator in validators:
            if CONDICTION_VALIDATORS[validator['type']]:
                params = dict(
                    [(key, value) for key, value in validator.items() if key != 'type']
                )
                CONDICTION_VALIDATORS[validator['type']](data, **params)
        return data

    return validate


def create_meta_class(model, exclude_fields=None):
    """构建序列化类的 Meta 类"""
    attrs = {'model': model, 'list_serializer_class': BulkCreateListSerializer}

    if exclude_fields is not None and isinstance(exclude_fields, (list, tuple)):
        attrs['exclude'] = exclude_fields
    else:
        attrs['fields'] = '__all__'

    return type('Meta', (object,), attrs)


def simple_support_m2m_field_specify_through_model(func):
    """
    简单的支持多对多字段指定了through_model
    TODO 如果中间表有必填字段，是会出错的
    :param func:
    :return:
    """
    @functools.wraps(func)
    def wrapper(model, action='create', batch=False, exclude_fields=None, **kwargs):
        if model._meta.many_to_many:
            field_info = get_field_info(model)
            for field in model._meta.many_to_many:
                if field_info.forward_relations[field.name].has_through_model:
                    related_model = field.related_model
                    kwargs[field.name] = serializers.PrimaryKeyRelatedField(many=True, required=not field.blank,
                                                                queryset=related_model.objects.all())
        return func(model, action, batch, exclude_fields=None, **kwargs)

    return wrapper


@simple_support_m2m_field_specify_through_model
def create_form_class(model, action='create', batch=False, exclude_fields=None, **kwargs):
    """构建序列化类"""

    def __init__(self, *args, **kwargs):
        """
        重置导出的字段映射，因为类似 BooleanField 字段，显示为中文会比较友好
        """
        self.serializer_field_mapping[JSONField] = drf_field.JSONField
        self.serializer_field_mapping[OriginJSONField] = DrfJSONField
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                if rfu_modes.append and attr in rfu_modes.append:
                    field.add(value)
                else:
                    field.set(value)
            else:
                setattr(instance, attr, value)
        instance.save()

        return instance

    attrs = {
        'Meta': create_meta_class(model, exclude_fields=None), 
        '__init__': __init__,
        'update': update
    }
    if action == 'update' and batch:
        attrs[model._meta.pk.name] = serializers.ModelSerializer.serializer_field_mapping[type(model._meta.pk)]()
    attrs.update(kwargs)

    class_name = f'{model.__name__}ModelSerializer'

    # 创建表单级的校验方法
    validators = get_gmeta_config_by_key(model, gmeta.GMETA_OBJECT_VALIDATORS)
    if validators:
        attrs['validate'] = get_validate(validators)
        # MethodType(get_validate(validators), cls)
    return type(class_name, (serializers.ModelSerializer,), attrs)


def get_form_class(model, action, exclude_fields=None, end=MANAGE_END_SLUG, request=None, batch=False, **kwargs):
    """获取表单类

    如果用户有自定义的表单类，则优先返回用户自定义的表单，如果没有，则使用默认创建的表单

    Params:
        model class 模型类
        action string 方法名
        exclude_fields list or tuple 排除的字段
        end string 端，指定是哪个端，有客户端和管理端

    Returns:
        class 表单类
    """
    # rfum_append=a,b
    rfum_append = request.query_params.get('rfum_append', None) if request.query_params else None
    if rfum_append:
        rfu_modes.append = rfum_append.split(',')
    else:
        rfu_modes.append = []

    name_suffix_map = {MANAGE_END_SLUG: 'ManageForm', CLIENT_END_SLUG: 'ClientForm'}

    action_map = {'create': 'Create', 'update': 'Update'}

    form_module = module.get_admin_module(model._meta.app_config.name, module.BSM_FORM)

    name_suffix = name_suffix_map.get(end)
    if not name_suffix:
        return create_form_class(model, action, batch=batch, exclude_fields=exclude_fields, **kwargs)

    class_name = '{}{}{}'.format(model.__name__, action_map[action], name_suffix)
    form_class = getattr(form_module, class_name, None)

    if form_class is None:
        return create_form_class(model, action, batch=batch, exclude_fields=exclude_fields, **kwargs)
    return form_class
