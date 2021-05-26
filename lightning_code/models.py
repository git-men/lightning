from django.db import models
from api_basebone.core.fields import UserField
from hashlib import md5
from api_basebone.export.specs import FieldType
# Create your models here.

TYPE_STRING = 'string'
TYPE_INT = 'integer'
TYPE_DECIMAL = 'decimal'
TYPE_BOOL = 'bool'
TYPE_REF = 'ref'
TYPE_DATE = 'date'
TYPE_IMAGE = 'image'

TYPE_CHOICES = (
    (TYPE_STRING, '字符串'),
    (TYPE_INT, '整数'),
    (TYPE_DECIMAL, '浮点数'),
    (TYPE_BOOL, '布尔值'),
    (TYPE_DATE, '日期'),
    (TYPE_REF, '数据'),
    (TYPE_IMAGE, '图片')
)

PROGRAMMING_LANGUAGES = (
    ('python', 'Python'),
    ('json', 'Json'),
    ('javascript', 'Javascript'),
    ('xml', 'XML')
)

class Category(models.Model):
    """代码目录
    """
    code = models.SlugField('代号', unique=True)
    name = models.CharField('名称', max_length=50)
    description = models.TextField('说明', blank=True, null=True)
    parent = models.ForeignKey('self', models.SET_NULL, verbose_name='上级目录', null=True, blank=True)
    
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('修改时间', auto_now=True)
    create_by = UserField(auto_current_add=True, verbose_name='创建人', on_delete=models.PROTECT, related_name='created_categories')
    update_by = UserField(auto_current=True, verbose_name='更新人', on_delete=models.PROTECT, related_name='updated_categories')

    class Meta:
        verbose_name = '目录'
        verbose_name_plural = '目录'
    
    class GMeta:
        title_field = 'name'


class Tag(models.Model):
    """标签
    """
    name = models.CharField('标签', max_length=50, unique=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    create_by = UserField(auto_current_add=True, verbose_name='创建人', on_delete=models.PROTECT)

    class Meta:
        verbose_name ='标签'
        verbose_name_plural ='标签'
    
    class GMeta:
        title_field = 'name'


class Function(models.Model):
    SCOPE_SERVER = 0
    SCOPE_FRONTEND = 1

    category = models.ForeignKey(Category, models.SET_NULL, verbose_name='目录', null=True, related_name='functions')
    name = models.SlugField('函数名', max_length=100, unique=True)
    scope = models.IntegerField('运行环境', choices=(
        (SCOPE_SERVER, '后端'),
        (SCOPE_FRONTEND, '前端')
    ))
    language = models.CharField('编程语言', max_length=30, default='python', choices=PROGRAMMING_LANGUAGES)
    description = models.TextField('说明', blank=True, null=True)
    code = models.TextField('代码', null=True, blank=True)
    released_code = models.TextField('已发布代码', null=True, blank=True)

    return_type = models.CharField('返回值类型', max_length=20, choices=TYPE_CHOICES)
    return_type_ref = models.CharField('返回值模型', max_length=50, blank=True, null=True)
    released_check_sum = models.CharField('发布版校验码', max_length=64, blank=True, null=True, default='')
    parameter_check_sum = models.CharField('参数校验码', max_length=64, blank=True, null=True, default='')

    version = models.PositiveIntegerField('版本', default=0)
    
    enable = models.BooleanField('启用', default=True)
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签')

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('修改时间', auto_now=True)
    create_by = UserField(auto_current_add=True, verbose_name='创建人', on_delete=models.PROTECT, related_name='created_functions')
    update_by = UserField(auto_current=True, verbose_name='更新人', on_delete=models.PROTECT, related_name='updated_functions')

    @property
    def check_sum(self):
        return md5(
            '|'.join([str(self.code.strip()), str(self.parameter_check_sum), self.return_type, str(self.return_type_ref)]).encode('utf-8')
        ).hexdigest()
    
    @property
    def released(self):
        return self.check_sum == self.released_check_sum
    
    class Meta:
        verbose_name = '函数'
        verbose_name_plural = '函数'
    
    class GMeta:
        title_field = 'name'
        computed_fields = [
            {'name': 'check_sum', 'type': FieldType.STRING, 'display_name': '校验码'},
            {'name': 'released', 'type': FieldType.BOOL, 'display_name': '已发布'}
        ]


class Parameter(models.Model):
    
    function = models.ForeignKey(Function, models.CASCADE, verbose_name='函数', related_name='parameters')
    name = models.SlugField('参数名', max_length=50)
    display_name = models.CharField('显示名', max_length=50, blank=True, null=True)
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES)
    ref = models.CharField('模型', max_length=50, blank=True, null=True)
    required = models.BooleanField('必填', default=True)
    default_value = models.TextField('默认值', null=True, blank=True)
    description = models.CharField('说明', max_length=1024, blank=True, null=True)

    @property
    def check_sum(self):
        return md5(
            '|'.join([self.name, self.type, str(self.ref), str(self.required), str(self.default_value)]).encode('utf-8')
        ).hexdigest()

    class Meta:
        index_together = ['function', 'name']
        verbose_name ='参数'
        verbose_name_plural ='参数'
    
    class GMeta:
        title_field = 'name'
        computed_fields = [
            {'name': 'check_sum', 'type': FieldType.STRING, 'display_name': '校验码'}
        ]
