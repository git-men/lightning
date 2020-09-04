"""
这里声明各种模型中 GMeta 中的配置的键的常量
"""


"""在序列化时，指定排除的字段，数据格式为列表或者元组"""
GMETA_SERIALIZER_EXCLUDE_FIELDS = 'exclude_fields'

"""输出 schema 中的 title_field，数据类型：字符串"""
GMETA_TITLE_FIELD = 'title_field'

"""
字段的重置配置，例如觉得字段默认的 verbose_name 不好看可以使用此配置，例子如下：

field_form_config = {
    'comments': {
        'verbose_name': '我是谁',
        'required': False,
    }
}
"""
GMETA_FIELD_CONFIG = 'field_form_config'

"""
django 中声明的字段的配置和输出配置键的映射

此常量供业务内部调用
"""
GMETA_FIELD_CONFIG_MAP = {
    'verbose_name': 'displayName'
}


"""
创建数据时，添加用户时，指定的用户的字段

数据类型：str

- 在创建数据时，根据指定的字段，自动插入用户的数据
"""
GMETA_CLIENT_USER_FIELD = 'client_user_field'

"""
筛选数据时，是否根据当前登录用户进行筛选

数据类型：bool
"""
GMETA_CLIENT_FILTER_BY_LOGIN_USER = 'client_filter_by_login_user'

"""
客户端接口不需要权限的设置

数据类型：tuple，其中元素为客户单视图中的视图方法，例如 create, update 等等这些

例如客户端首页的商品是不需要权限就可以浏览的，此时配置如下：

client_api_permission_skip = ('list', 'set', 'retrieve')
"""
GMETA_CLIENT_API_PERMISSION_SKIP = 'client_api_permission_skip'


"""
客户端接口认证的设置

数据类型：tuple 其中元素为客户视图中的视图方法，例如 create, update 等等这些

例如客户端有些模型的删除接口禁止访问，此时配置如下

client_api_no_authentication = ('destroy', )
"""
GMETA_CLIENT_API_NO_AUTHENTICATION = 'client_api_no_authentication'

"""
客户端接口允许调用的方法，默认使用白名单模式

数据类型：tuple 其中元素为客户视图中的视图方法，例如 create, update 等等这些

例如客户端有些模型只允许创建和更新接口，此时配置如下

client_api_authenticate_methods = ('create', 'update')
"""
GMETA_CLIENT_API_AUTHENTICATE_METHODS = 'client_api_authenticate_methods'

"""计算属性，即@property函数，只允许读，不允许写，配置方式：
computed_fields = (
    {'func_name', 'type', 'displayName', 'choices'},
)
"""
GMETA_COMPUTED_FIELDS = 'computed_fields'

"""
使用Django的annotate来作计算字段
annotated_fields = {
    'distribution_num': {
        'display_name': '分销收益次数',
        'annotation': models.Count('walletbill'),
        'type': FieldType.INTEGER,
    }
}
"""
GMETA_ANNOTATED_FIELDS = 'annotated_fields'

GMETA_OBJECT_VALIDATORS = 'validators'

"""
managers, 对应不同场景下，有不同的queryset,结构如下：
managers = {
    'client_api': xxxx,
    'manager_api': yyyy,
}
"""
GMETA_MANAGERS = 'managers'

"""管理端导出文件指定的扩展字段 列表 List

manage_export_expand_fields = []
"""
GMETA_MANAGE_EXPORT_EXPAND_FIELDS = 'manage_export_expand_fields'


"""管理端导出文件指定的字段 列表 List

manage_export_expand_fields = []
"""
GMETA_MANAGE_EXPORT_FIELDS = 'manage_export_fields'


"""管理端迭代模型反向关系字段名称 字符串 str

manage_export_reverse_field = []
"""
GMETA_MANAGE_REVERSE_FIELD = 'manage_export_reverse_field'


"""管理端模型反向关系字段和顶级字段的映射 字典 dict

manage_export_reverse_fields_map = []
"""
GMETA_MANAGE_REVERSE_FIELDS_MAP = 'manage_export_reverse_fields_map'

GMETA_CREATOR_FIELD = 'creator_field'
GMETA_UPDATER_FIELD = 'updater_field'
