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
创建数据时，添加用户时，指定的用户的字段，作用有以下两个方面

数据类型：str

- 在创建数据时，根据指定的字段，自动插入用户的数据
- 在获取数据时，根据指定的字段，根据当前用户，筛选对应的数据
"""
GMETA_AUTO_ADD_CURRENT_USER = 'auto_add_current_user'

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

GMETA_OBJECT_VALIDATORS = 'validators'

"""
managers, 对应不同场景下，有不同的queryset,结构如下：
managers = {
    'client_api': xxxx,
    'manager_api': yyyy,
}
"""
GMETA_MANAGERS = 'managers'
