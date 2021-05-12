"""
重要的事情说三遍

这是一份参考协议声明，即后端根据这份协议生成出对应的配置
"""

class FieldType:
    STRING = 'string'
    TEXT = 'text'
    RICHTEXT = 'richtext'
    BOOL = 'bool'
    INTEGER = 'integer'
    FLOAT = 'float'
    DECIMAL = 'decimal'
    DATE = 'date'
    DATETIME = 'datetime'
    TIME = 'time'
    IMAGE = 'image'
    FILE = 'file'
    REF = 'ref'
    MREF = 'mref'
    DURATION = 'duration'


common_attribute = [
    {
        'name': 'required',
        'type': 'bool',
        'required': False,
        'default': False,
    },
    {
        'name': 'name',
        'type': 'string',
        'required': True,
    },
    {
        'name': 'displayName',
        'type': 'string',
        'required': False,
    },
    {
        'name': 'default',
        'type': 'object',
        'required': False,
    },
    {
        'name': 'helpText',
        'type': 'string',
        'required': False,
    },
    {
        'name': 'choices',
        'type': 'array',
        'required': False,
    },
    {
        'name': 'editable',
        'type': 'bool',
        'required': False,
    },
    {
        'name': 'readonly',
        'type': 'bool',
        'required': False,
        'default': False
    }
]

# 定义字段类型，每个字段类型有其自身的参数及意义。
FIELDS = {
    'String': {
        'name': 'string',
        'displayName': '字符串',
        'attributes': [
            {
                'name': 'maxLength',
                'type': 'integer',
                'required': True,
            },
        ],
    },
    'Text': {
        'name': 'text',
        'displayName': '长文本',
    },
    'RichText': {
        'name': 'richtext',
        'displayName': '富文本',
    },
    'Integer': {
        'name': 'integer',
        'displayName': '整型',
    },
    'Float': {
        'name': 'float',
        'displayName': '浮点型',
    },
    'Decimal': {
        'name': 'decimal',
        'displanName': '小数',
    },
    'Bool': {
        'name': 'bool',
        'displayName': '布尔型',
    },
    'Date': {
        'name': 'date',
    },
    'Time': {
        'name': 'time',
    },
    'DateTime': {
        'name': 'datetime',
    },
    'Image': {
        'name': 'image',
    },
    'File': {
        'name': 'file',
    },
    'Ref': {
        'name': 'ref',
        'attributes': [
            {
                'name': 'ref',
                'type': 'string',
                'required': False,
            },
        ],
    },
    'RefMult': {
        'name': 'mref',
        'attributes': [
            {
                'name': 'ref',
                'type': 'string',
                'required': False,
            },
        ],
    },
    'RefOne': {
        'name': 'oref',
        'attributes': [
            {
                'name': 'ref',
                'type': 'string',
                'required': False,
            },
        ],
    },
    'Object': {
        'name': 'object',
    },
    'Array': {
        'name': 'array',
    },
    'TimeStamp': {
        'name': 'timestamp',
        'displayName': '时间戳'
    }
}
