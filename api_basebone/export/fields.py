import inspect
import types
import logging
from django.apps import apps
from django.db.models.fields import NOT_PROVIDED

from api_basebone.core import gmeta
from api_basebone.core.decorators import BSM_ADMIN_COMPUTED_FIELDS_MAP
from api_basebone.utils.format import underline_to_camel
from api_basebone.utils.meta import (
    get_concrete_fields,
    get_export_apps,
    get_reverse_fields,
    get_field_by_reverse_field,
)
from api_basebone.core.fields import ObjectField, ArrayField

from .specs import FIELDS

log = logging.getLogger(__name__)

# 默认的 django 字段类型
DEFAULT_DJANOG_FIELD_TYPE = 'Text'

DJANGO_FIELD_TYPE_MAP = {
    'AutoField': 'Integer',
    'BigAutoField': 'String',
    'BooleanField': 'Bool',
    'NullBooleanField': 'Bool',
    'CharField': 'String',
    'SlugField': 'String',
    'DateField': 'Date',
    'EmailField': 'String',
    'DateTimeField': 'DateTime',
    'FloatField': 'Float',
    'DecimalField': 'Decimal',
    'GenericIPAddressField': 'String',
    'SmallIntegerField': 'Integer',
    'IntegerField': 'Integer',
    'BigIntegerField': 'String',
    'PositiveIntegerField': 'Integer',
    'PositiveSmallIntegerField': 'Integer',
    'TextField': 'Text',
    'TimeField': 'Time',
    'URLField': 'String',
    'UUIDField': 'String',
    'ForeignKey': 'Ref',
    'TreeForeignKey': 'Ref',
    'OneToOneField': 'RefOne',
    'ManyToManyField': 'RefMult',
    'BoneRichTextField': 'RichText',
    'BoneImageUrlField': 'Image',
    'BoneFileUrlField': 'File',
    'JsonObjectField': 'Object',
    'JsonArrayField': 'Array',
    'BoneTimeStampField': 'TimeStamp',
    'UserField': 'Ref',
}

VALIDATOR_MAP = {
    'django.core.validators.RegexValidator': 'regex',
    'django.core.validators.EmailValidator': 'email',
    'django.core.validators.URLValidator': 'url',
    'django.core.validators.validate_email': 'email',
    'django.core.validators.validate_slug': 'slug',
    'django.core.validators.validate_unicode_slug': 'unicode_slug',
    'django.core.validators.validate_ipv4_address': 'ip',
    'django.core.validators.validate_ipv6_address': 'ip',
    'django.core.validators.validate_ipv46_address': 'ip',
    'django.core.validators.validate_comma_separated_integer_list': '',  # 未支持
    'django.core.validators.int_list_validator': '',  # 未支持
    'django.core.validators.MaxValueValidator': 'max_value',
    'django.core.validators.MinValueValidator': 'min_value',
    # 以下几个属性，与Model中定义的属性重复了，暂隐藏
    # 'django.core.validators.MaxLengthValidator': 'max_length',
    # 'django.core.validators.MinLengthValidator': 'min_length',
    # 'django.core.validators.DecimalValidator': 'decimal',
    'django.core.validators.FileExtensionValidator': '',  # 未支持
    'django.core.validators.validate_image_file_extension': '',  # 未支持
    'django.core.validators.ProhibitNullCharactersValidator': '',  # 未支持
}


def get_attr_in_gmeta_class(model, config_name, default_value=None):
    """获取指定模型 GMeta 类中指定的属性

    Params:
        model class django 模型类
        config_name string GMeta 类中配置项的名称
        default_value 任何数据类型 默认数据
    """

    gmeta_class = getattr(model, 'GMeta', None)
    if not gmeta_class:
        return default_value
    return getattr(gmeta_class, config_name, default_value)


class FieldConfig:
    def reset_field_config(self, field, data_type=None):
        """根据 Gmeta 中声明的字段的配置进行重置"""
        field_config = get_attr_in_gmeta_class(
            field.model, gmeta.GMETA_FIELD_CONFIG, {}
        ).get(field.name, {})
        if not field_config:
            return field_config

        # 做 django 中的写法和输出的配置的转换
        result = {
            gmeta.GMETA_FIELD_CONFIG_MAP[key]
            if key in gmeta.GMETA_FIELD_CONFIG_MAP
            else key: value
            for key, value in field_config.items()
        }
        return result

    def validator_config(self, field):
        """获取字段的校验规则
        """
        if not getattr(field, 'validators', None):
            return []
        validators = []
        for validator in field.validators:
            if type(validator).__name__ == 'function':
                key = '.'.join([validator.__module__, validator.__name__])
            else:
                target = validator.__class__
                key = '.'.join([target.__module__, target.__name__])
            if key not in VALIDATOR_MAP or not VALIDATOR_MAP[key]:
                continue
            attrs = {}
            rule_name = VALIDATOR_MAP[key]
            attrs['type'] = rule_name

            # 个别校验器需要带上一些参数
            if rule_name in ['min_value', 'max_value', 'max_length', 'min_length']:
                attrs.update({'value': validator.limit_value})

            if rule_name == 'regex':
                attrs.update(
                    {
                        'regex': validator.regex.pattern,
                        'inverse_match': validator.inverse_match,
                        'flags': validator.flags,
                    }
                )

            if rule_name == 'decimal':
                attrs['max_digits'] = validator.max_digits
                attrs['decimal_places'] = validator.decimal_places

            validators.append(attrs)
        return validators

    def _check_is_function(self, func):
        if inspect.isfunction(func):
            return True

        func_types = (
            types.BuiltinFunctionType,
            types.BuiltinMethodType,
            types.MethodType,
        )
        if isinstance(func, func_types):
            return True
        return False

    def _get_common_field_params(self, field, data_type):
        """获取字段的通用的配置"""
        config = {
            'name': field.name,
            'displayName': field.verbose_name,
            'required': not field.blank,
            'primaryKey': field.primary_key,
            'type': data_type,
            'help': field.help_text,
        }

        if field.choices:
            config['choices'] = field.choices

        if not field.editable:
            config['editable'] = field.editable
        elif hasattr(field, 'get_bsm_internal_type') and field.get_bsm_internal_type() == 'UserField' and (field.auto_current or field.auto_current_add):
            # 直接搞editable=False会导致drf生成form时不序列化此字段，insert_user_info会无效，所以临时先这么干
            config['editable'] = False

        validator_config = self.validator_config(field)
        if validator_config:
            config['validators'] = validator_config

        if field.default is not NOT_PROVIDED:
            if inspect.isclass(field.default):
                config['default'] = field.default()
            elif not self._check_is_function(field.default):
                config['default'] = field.default
        return config

    def normal_field_params(self, field, data_type):
        """通用普通字段的配置获取"""
        base = self._get_common_field_params(field, data_type)
        base.update(self.reset_field_config(field, data_type))
        return base

    def string_params(self, field, data_type):
        """字符型字段的配置获取"""
        base = self._get_common_field_params(field, data_type)
        base['maxLength'] = field.max_length
        base.update(self.reset_field_config(field, data_type))
        return base

    def decimal_params(self, field, data_type):
        """小数类型的配置获取
        """
        base = self._get_common_field_params(field, data_type)
        base['precision'] = field.decimal_places
        base['maxDigits'] = field.max_digits
        base.update(self.reset_field_config(field, data_type))
        return base

    def ref_params(self, field, data_type):
        """外键关联字段的配置获取"""
        base = self._get_common_field_params(field, data_type)
        meta = field.related_model._meta
        base['ref'] = '{}__{}'.format(meta.app_label, meta.model_name)
        base['refField'] = field.remote_field.name
        base['refTo'] = field.remote_field.field_name
        base.update(self.reset_field_config(field, data_type))
        return base

    def refmult_params(self, field, data_type):
        """多对多字段的配置获取"""
        base = self._get_common_field_params(field, data_type)
        meta = field.related_model._meta
        base['ref'] = '{}__{}'.format(meta.app_label, meta.model_name)
        base['refField'] = field.remote_field.name
        base['refTo'] = field.m2m_reverse_target_field_name()
        base.update(self.reset_field_config(field, data_type))
        return base

    def refone_params(self, field, data_type):
        """一对一"""
        return self.ref_params(field, data_type)

    def object_params(self, field, data_type):
        """对象类型的配置获取
        """
        base = self._get_common_field_params(field, data_type)
        base['ref'] = f'object_model__{field.object_model.__name__}'.lower()
        base.update(self.reset_field_config(field, data_type))
        return base

    def array_params(self, field, data_type):
        """数组类型的配置获取
        """
        base = self._get_common_field_params(field, data_type)
        base['ref'] = f'array_item_model__{field.item_model.__name__}'.lower()
        base['item_type'] = field.item_type
        base.update(self.reset_field_config(field, data_type))
        return base


field_config_instance = FieldConfig()


def get_model_field_config(model):
    """获取指定模型的字段配置, 字段输出所有的字段，包含反向字段

    Params:
        model class django 模型类
    """
    fields = get_concrete_fields(model)
    key = '{}__{}'.format(model._meta.app_label, model._meta.model_name)
    if (not model._meta.app_label):
        key = model._meta.model_name

    title_field = get_attr_in_gmeta_class(model, gmeta.GMETA_TITLE_FIELD, None)
    if title_field is None:
        title_field = model._meta.pk.name if getattr(model._meta, 'pk', None) else None

    config = []
    for item in fields:
        field_type = None
        # 抓取 internal_type
        field_type_func = getattr(item, 'get_bsm_internal_type', None)
        if field_type_func:
            field_type = DJANGO_FIELD_TYPE_MAP.get(item.get_bsm_internal_type())
        else:
            field_type = DJANGO_FIELD_TYPE_MAP.get(item.get_internal_type())

        if field_type is not None:
            data_type = FIELDS.get(field_type)['name']
            function = getattr(
                field_config_instance, '{}_params'.format(field_type.lower()), None
            )
            if function is not None:
                config.append(function(item, data_type))
            else:
                config.append(field_config_instance.normal_field_params(item, data_type))

    # 添加反转字段
    reverse_fields = get_reverse_fields(model)
    if reverse_fields:
        for item in reverse_fields:
            reverse_config = {'name': item.name, 'required': False, 'type': 'bref'}

            if item.many_to_many:
                reverse_config['type'] = 'mref'

            elif item.one_to_one:
                reverse_config['type'] = 'boref'

            meta = item.related_model._meta
            reverse_config['ref'] = '{}__{}'.format(meta.app_label, meta.model_name)
            reverse_config['refField'] = item.remote_field.name
            # TODO bref 下还是不应该要有refTo了，但是为了保留兼容性，可以先保留代码
            if item.one_to_one or item.one_to_many:
                reverse_config['refTo'] = item.field_name or meta.pk and meta.pk.name
                reverse_config['displayName'] = '{}({})'.format(meta.verbose_name, item.remote_field.verbose_name)
            elif item.many_to_many:
                reverse_config['refTo'] = item.field.m2m_target_field_name()
                reverse_config['displayName'] = meta.verbose_name
            reverse_config.update(field_config_instance.reset_field_config(item))
            config.append(reverse_config)

    # 添加 model 中  GMETA 中设置的只读属性
    computed_fields = get_attr_in_gmeta_class(model, gmeta.GMETA_COMPUTED_FIELDS, [])
    for field in computed_fields:
        attrs = {
            'name': field['name'],
            'type': field['type'],
            'required': False,
            'readonly': True,
            'displayName': field.get('display_name', field['name']),
        }
        if 'choices' in field:
            attrs['choices'] = field['choices']
        config.append(attrs)

    # 添加 admin 冲设置的计算只读属性
    admin_computed_fields = getattr(model, BSM_ADMIN_COMPUTED_FIELDS_MAP, {})
    for name, field_value in admin_computed_fields.items():
        attrs = {
            'name': name,
            'type': field_value['field_type'],
            'required': False,
            'readonly': True,
            'displayName': field_value['display_name'],
        }
        config.append(attrs)

    # 添加 annotated_field
    annotated_fields = get_attr_in_gmeta_class(model, gmeta.GMETA_ANNOTATED_FIELDS, {})
    for name, field in annotated_fields.items():
        attrs = {'required': False, 'readonly': True, 'name': name}
        attrs.update({underline_to_camel(k): v for k, v in field.items()})
        attrs.setdefault('displayName', name)
        del attrs['annotation']
        config.append(attrs)

    ret = {
        'name': key,
        'displayName': model._meta.verbose_name,
        'titleField': title_field,
        'fields': config,
    }

    # 添加全局校验规则
    validators = get_attr_in_gmeta_class(model, gmeta.GMETA_OBJECT_VALIDATORS)
    if validators:
        ret['validators'] = validators

    return {key: ret}


def get_app_field_schema():
    """输出应用模型配置"""
    config, export_apps = {}, get_export_apps()
    if not export_apps:
        return config

    for item in export_apps:
        app = apps.get_app_config(item)
        for model in app.get_models():
            config.update(get_model_field_config(model))
    return config


def get_app_json_field_schema():
    """输出应用模型json field配置"""

    def generate_object_field_schema(models):
        config = {}
        for model in models:
            object_fields = [
                field
                for field in get_concrete_fields(model)
                if isinstance(field, ObjectField)
            ]
            for field in object_fields:
                if field.object_model:
                    config.update(get_model_field_config(field.object_model))
                    config.update(generate_object_field_schema([field.object_model]))
        return config

    def generate_array_field_schema(models):
        config = {}
        for model in models:
            array_fields = [
                field
                for field in get_concrete_fields(model)
                if isinstance(field, ArrayField)
            ]
            for field in array_fields:
                if field.item_model:
                    config.update(get_model_field_config(field.item_model))
        return config

    object_field_config, array_field_config, export_apps = {}, {}, get_export_apps()
    if not export_apps:
        return {}

    for item in export_apps:
        app = apps.get_app_config(item)
        models = app.get_models()
        models = list(models)
        object_field_config.update(generate_object_field_schema(models))
        array_field_config.update(generate_array_field_schema(models))

    return (
        {f'object_model__{key}': value for key, value in object_field_config.items()},
        {f'array_item_model__{key}': value for key, value in array_field_config.items()},
    )

