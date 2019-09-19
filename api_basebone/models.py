import logging

from django.conf import settings
from django.db import models
from api_basebone.core.fields import JSONField


logger = logging.getLogger('django')


class AdminLog(models.Model):

    action_time = models.DateTimeField('发生时间', auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='用户')

    action = models.CharField('动作', max_length=20, blank=True, default='')
    app_label = models.CharField('应用标识', max_length=20, blank=True, default='')
    model_slug = models.CharField('模型标识', max_length=30, blank=True, default='')
    object_id = models.CharField('数据ID', max_length=20, blank=True, default='')
    message = models.CharField('消息', max_length=50, blank=True, default='')
    params = JSONField(default={})

    class Meta:
        verbose_name = '动作日志记录'
        verbose_name_plural = '动作日志记录'


class Api(models.Model):
    '''Api接口模型'''

    OPERATION_LIST = 'list'
    OPERATION_RETRIEVE = 'retrieve'
    OPERATION_CREATE = 'create'
    OPERATION_UPDATE = 'update'
    OPERATION_REPLACE = 'replace'
    OPERATION_DELETE = 'delete'
    OPERATION_BATCH_UPDATE = 'batch_update'
    OPERATION_BATCH_DELETE = 'batch_delete'
    OPERATION_FUNC = 'func'
    OPERATIONS_CHOICES = (
        (OPERATION_LIST, '查看'),
        (OPERATION_RETRIEVE, '详情'),
        (OPERATION_CREATE, '新建'),
        (OPERATION_UPDATE, '全部更新'),
        (OPERATION_REPLACE, '部分更新'),
        (OPERATION_DELETE, '删除'),
        (OPERATION_BATCH_UPDATE, '批量更新'),
        (OPERATION_BATCH_DELETE, '批量删除'),
        (OPERATION_FUNC, '云函数'),
    )

    MATHOD_GET = 'get'
    MATHOD_POST = 'post'
    MATHOD_PUT = 'put'
    MATHOD_DELETE = 'delete'
    MATHOD_PATCH = 'patch'

    METHOD_MAP = {
        OPERATION_LIST: MATHOD_GET,
        OPERATION_RETRIEVE: MATHOD_GET,
        OPERATION_CREATE: MATHOD_POST,
        OPERATION_UPDATE: MATHOD_PUT,
        OPERATION_REPLACE: MATHOD_PATCH,
        OPERATION_DELETE: MATHOD_DELETE,
        OPERATION_BATCH_UPDATE: MATHOD_PUT,
        OPERATION_BATCH_DELETE: MATHOD_DELETE,
        OPERATION_FUNC: MATHOD_POST,
    }

    slug = models.SlugField('接口标识', max_length=50, unique=True)
    app = models.CharField('app名字', max_length=50)
    model = models.CharField('数据模型名字', max_length=50)
    operation = models.CharField('操作', max_length=20, choices=OPERATIONS_CHOICES)
    ordering = models.CharField('排序', max_length=50, blank=True, default='')
    func_name = models.CharField('云函数名称', max_length=50, blank=True, default='')

    def __str__(self):
        return self.slug

    @property
    def method(self):
        '''API提交的方法'''
        return self.METHOD_MAP.get(self.operation, '')

    def get_order_by_fields(self):
        return self.ordering.split(',')

    class Meta:
        verbose_name = 'Api接口模型'
        verbose_name_plural = 'Api接口模型'


class Parameter(models.Model):
    '''参数'''

    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_DECIMAL = 'decimal'
    TYPE_BOOLEAN = 'boolean'
    TYPE_PAGE_SIZE = 'PAGE_SIZE'
    TYPE_PAGE_IDX = 'PAGE_IDX'
    TYPE_PK = 'pk'

    api = models.ForeignKey(Api, models.PROTECT, verbose_name='api')
    name = models.CharField('参数名', max_length=50)
    desc = models.CharField('备注', max_length=100)
    type = models.CharField('参数类型', max_length=100)
    required = models.BooleanField('是否必填', default=True)
    default = models.CharField('默认值', max_length=50, null=True, default='')

    def is_special_defined(self):
        """自定义参数，用于特殊用途"""
        return self.type in (self.TYPE_PAGE_SIZE, self.TYPE_PAGE_IDX, self.TYPE_PK)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '参数'
        verbose_name_plural = '参数'


class Field(models.Model):
    '''API的字段'''

    api = models.ForeignKey(Api, models.PROTECT, verbose_name='api')
    name = models.CharField('字段名', max_length=200)
    value = models.CharField('赋值', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'API的字段'
        verbose_name_plural = 'API的字段'
        ordering = ['name']  # 排序很重要，确保同一个分支的列会排在一起，且层级少的排在前面


class Filter(models.Model):
    '''查询条件'''

    TYPE_CONTAINER = 0  # 容器
    TYPE_CHILD = 1  # 单一条件

    # OPERATIONS_AND = 'and'
    # OPERATIONS_OR = 'or'
    # OPERATIONS_GT = '>'
    # OPERATIONS_GTE = '>='
    # OPERATIONS_LT = '<'
    # OPERATIONS_LTE = '<='
    # OPERATIONS_EQ = '='
    # OPERATIONS_NOT_EQ = '!='
    # OPERATIONS_IN = 'in'
    # OPERATIONS_STARTSWITH = 'startswith'
    # OPERATIONS_ENDSWITH = 'endswith'
    # OPERATIONS_CONTAINS = 'contains'
    # OPERATIONS_ICONTAINS = 'icontains'
    # OPERATIONS_BETWEEN = 'between'
    # OPERATIONS_NEAR = 'near'
    # OPERATIONS_HAS = 'has'
    # OPERATIONS_HAS_ANY = 'has_any'
    # OPERATIONS_HAS_ALL = 'has_all'
    # OPERATIONS_ISNULL = 'isnull'
    # OPERATIONS_CHOICES = (
    #     (OPERATIONS_AND, '与'),
    #     (OPERATIONS_OR, '或'),
    #     (OPERATIONS_GT, '大于'),
    #     (OPERATIONS_GTE, '大于等于'),
    #     (OPERATIONS_LT, '小于'),
    #     (OPERATIONS_LTE, '小于等于'),
    #     (OPERATIONS_EQ, '等于'),
    #     (OPERATIONS_NOT_EQ, '不等于'),
    #     (OPERATIONS_IN, '在列表范围内'),
    #     (OPERATIONS_STARTSWITH, '以某字符串开始'),
    #     (OPERATIONS_ENDSWITH, '以某字符串结束'),
    #     (OPERATIONS_CONTAINS, '包含'),
    #     (OPERATIONS_ICONTAINS, '包含（无视大小写）'),
    #     (OPERATIONS_BETWEEN, '起止范围'),
    #     # (OPERATIONS_NEAR, ''),
    #     # (OPERATIONS_HAS, ''),
    #     # (OPERATIONS_HAS_ANY, ''),
    #     # (OPERATIONS_HAS_ALL, ''),
    #     (OPERATIONS_ISNULL, '为空'),
    # )

    api = models.ForeignKey(Api, models.CASCADE, verbose_name='api')
    type = models.IntegerField(
        '条件类型', choices=((TYPE_CONTAINER, '容器'), (TYPE_CHILD, '单一条件'))
    )
    parent = models.ForeignKey(
        'self', models.CASCADE, null=True, verbose_name='parent', related_name="children"
    )
    field = models.CharField('条件字段名', max_length=50, null=True)
    # operator = models.CharField('条件判断符', max_length=20, choices=OPERATIONS_CHOICES)
    operator = models.CharField('条件判断符', max_length=20)
    value = models.CharField('条件值', max_length=100, null=True)
    layer = models.IntegerField('嵌套层数', default=0)

    def __str__(self):
        if self.type == self.TYPE_CONTAINER:
            return '{self.operator}'
        elif self.type == self.TYPE_CHILD:
            return f'{self.field} {self.operator} {self.value}'
        else:
            return ''

    class Meta:
        verbose_name = 'API的查询条件'
        verbose_name_plural = 'API的查询条件'
