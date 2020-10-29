import uuid
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


def uuid4_hex():
    return uuid.uuid4().hex


class Block(MPTTModel):
    id = models.SlugField('标识', unique=True, primary_key=True, default=uuid4_hex)
    component = models.CharField('组件', max_length=20, default='')  # 20个字符已经很过分了
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, related_name='children', verbose_name='父结点')

    def __str__(self):
        return f'<{self.component}: ({self.id})>'

    class Meta:
        verbose_name = '渲染块'
        verbose_name_plural = verbose_name


class Page(models.Model):
    root = models.ForeignKey(Block, verbose_name='根结点', on_delete=models.CASCADE)
    name = models.CharField('名称', max_length=50)

    class Meta:
        verbose_name = '页面'
        verbose_name_plural = verbose_name
