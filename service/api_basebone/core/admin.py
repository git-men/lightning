from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.utils import six

# meta 扩展的常量声明

# 根据哪个字段进行筛选登录的用户，因为一个模型可能有多个字段指向用户模型
GMETA_AUTH_FILTER_FIELD = 'gmeta_auth_filter_field'


ATTRS_DICT = {
    GMETA_AUTH_FILTER_FIELD: None
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
