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

- 在创建数据时，根据指定的字段，自动插入用户的数据
- 在获取数据时，根据指定的字段，根据当前用户，筛选对应的数据
"""
GMETA_AUTO_ADD_CURRENT_USER = 'auto_add_current_user'

"""
客户端接口不需要权限的设置

数据结构为元组，其中元素为客户单视图中的视图方法，例如 create, update 等等这些
"""
GMETA_CLIENT_API_PERMISSION_SKIP = 'client_api_permission_skip'
