from django.conf import settings
from django.db import models


class Tag(models.Model):

    name = models.CharField('名称', max_length=20)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'

    def __str__(self):
        return self.name


class Category(models.Model):

    name = models.CharField('名称', max_length=20)
    show = models.BooleanField('是否显示', default=True)
    parent = models.ForeignKey('self', verbose_name='上级分类', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'

    def __str__(self):
        return self.name


class Article(models.Model):

    title = models.CharField('标题', max_length=50)
    index_pic = models.URLField('封面', blank=True, default='')
    summary = models.CharField('摘要', max_length=50)
    content = models.TextField('内容')

    is_public = models.BooleanField('已发布', default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='作者',
        on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, verbose_name='标签')
    categories = models.ManyToManyField(Category, verbose_name='所属分类')

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'

    def __str__(self):
        return self.title
