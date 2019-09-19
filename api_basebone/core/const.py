"""
各种常量说明
"""

"""客户端传入过滤条件的关键字

客户端可通过此进行数据过滤和筛选

支持的方法：POST 当前适用于列表方法
数据格式 List:

    [
        {
            'field': 字段名,
            'operator': 运算符,
            'value': 值,
        },
        ...
    ]
"""
FILTER_CONDITIONS = 'filters'

"""客户端传入排除条件的关键字

客户端可通过此进行数据排除

支持的方法：POST 当前适用于列表方法
数据格式 List:

    [
        {
            'field': 字段名,
            'operator': 运算符,
            'value': 值,
        },
        ...
    ]
"""
EXCLUDE_CONDITIONS = 'excludes'

"""客户端传入展示字段的关键字
"""
DISPLAY_FIELDS = 'display_fields'

"""展开字段的传入

支持的方法：POST 当前适用于列表方法

数据格式 List：[字段名, 字段名.字段名, 字段名, ...]
"""
EXPAND_FIELDS = 'expand_fields'

"""排序字段

支持的方法：POST 当前适用于列表方法

数据格式 List：[字段名, 字段名, ....]
"""
ORDER_BY_FIELDS = 'order_by'

"""客户端请求的数据结构为树形

支持的方法：POST, GET 当前适用于列表方法

数据格式 Bool：true 或者 false
"""
DATA_WITH_TREE = 'data_with_tree'

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

"""django 中声明的字段的配置和输出配置键的映射

此常量供业务内部调用
"""
GMETA_FIELD_CONFIG_MAP = {'verbose_name': 'displayName'}

"""
api接口中，条件更新的接口update_by_condition中采用，表示update语句set的列值对
"""
SET_FIELDS = 'set_fields'
