from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.utils import six

# meta 扩展的常量声明

# 根据哪个字段进行筛选登录的用户，因为一个模型可能有多个字段指向用户模型
GMETA_AUTH_FILTER_FIELD = 'auth_filter_field'

# 声明父亲字段和 related_name 的属性，数据结构如下：
# (
#   (指向自身的字段，指向自身字段的 related_name, 默认值),
#   ...
# )
# 默认为一个空的元组
GMETA_PARENT_ATTR_MAP = 'parent_attr_map'

ATTRS_DICT = {
    GMETA_AUTH_FILTER_FIELD: None,
    GMETA_PARENT_ATTR_MAP: (),
}


class BaseMetaclass(type):

    def __new__(cls, name, bases, attrs):
        base_attrs = ATTRS_DICT
        base_attrs.update(attrs)
        return super(BaseMetaclass, cls).__new__(cls, name, bases, base_attrs)


class ModelAdmin(DjangoModelAdmin):

    @six.add_metaclass(BaseMetaclass)
    class GMeta:
        pass
