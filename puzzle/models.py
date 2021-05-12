import uuid
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from puzzle import component_resolver
from jsonfield import JSONField


def uuid4_hex():
    return uuid.uuid4().hex


class Block(MPTTModel):
    COMPONENT_NAME = None

    id = models.SlugField('标识', unique=True, primary_key=True, default=uuid4_hex)
    component = models.CharField('组件', max_length=20, default='')  # 20个字符已经很过分了
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父结点')

    def __str__(self):
        return f'<{self.component}: ({self.id})>'

    def save(self, *args, **kwargs):
        if self.COMPONENT_NAME: 
            self.component = self.COMPONENT_NAME
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = '渲染块'
        verbose_name_plural = verbose_name


class Page(Block):
    COMPONENT_NAME = 'Page'

    name = models.CharField('名称', max_length=50)

    class Meta:
        verbose_name = '页面'
        verbose_name_plural = verbose_name
    
    class GMeta:
        title_field = 'name'


class Table(models.Model):
    block = models.OneToOneField(Block, verbose_name='渲染结点', null=True, on_delete=models.CASCADE)
    model = models.CharField('模型', max_length=255)
    title = models.CharField('标题', max_length=255, null=True)
    display = JSONField('列表字段', default=[])
    filter = JSONField('过滤字段', default=[])
    inlineActions = JSONField('操作项', default=[])
    actions = JSONField('批量操作', default=[])
    tableActions = JSONField('全局操作', default=[])
    sortable = JSONField('排序字段', default=[])
    filterLayout = models.CharField('滤布局',  max_length=255, default='default')

    class Meta:
        verbose_name = '表格'
        verbose_name_plural = verbose_name

    class GMeta:
        title_field = 'title'


@component_resolver('Table')
def table_resolver(block: Block):
    table = Table.objects.get(block__id=block.id)
    return {
        'model': table.model,
        'table_id': table.id,
        'display': table.display,
        'filter': table.filter,
        'inlineActions': table.inlineActions,
        'actions': table.actions,
        'tableActions': table.tableActions,
        'sortable': table.sortable,
        'filterLayout': table.filterLayout,
        'title': table.title
    }

