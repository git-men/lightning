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


GMETA_SERIALIZER_EXCLUDE_FIELDS = 'exclude_fields'
