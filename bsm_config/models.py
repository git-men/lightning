"""
BSM体系的配置，都可以存储至数据库，包括：
1. 菜单
2. 管理后台的配置
3. 客户端接口的开放
4. 甚至数据模型的结构等。
"""

from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps.registry import apps

from api_basebone.core.fields import JSONField
from api_basebone.export.specs import FieldType

# 自定义菜单
class Menu(models.Model):
    """存储管理后台左侧导航菜单栏的结构
    """

    name = models.CharField('名称', max_length=30, null=True, blank=True)
    icon = models.CharField(
        '图标名',
        max_length=100,
        null=True,
        blank=True,
        help_text='请使用AntDesign的图标:https://ant.design/components/icon-cn/',
    )
    parent = models.ForeignKey(
        'self', models.SET_NULL, null=True, blank=True, verbose_name='上级菜单', related_name='children'
    )
    page = models.CharField(
        '页面', max_length=200, help_text='前端功能页面的标识', default='list', null=True, blank=True, choices=[
            ['list', '列表页'], ['detail', '详情页'], ['adminConfig', '页面配置面板'], ['auto', '自定义页面']
        ]
    )
    path = models.CharField('自定义路径', max_length=255, null=True, blank=True)
    permission = models.CharField(
        '关联权限',
        max_length=200,
        help_text='格式有<app_label>.<codename>',
        blank=True,
        null=True,
    )
    model = models.CharField(
        '关联模型',
        max_length=200,
        help_text='格式为：<app_label>__<model>',
        blank=True,
        null=True,
    )
    sequence = models.IntegerField('排序', default=1000, help_text='数值越小，排列越前')

    class Meta:
        verbose_name = '导航菜单'
        verbose_name_plural = '导航菜单'

    class GMeta:
        title_field = 'name'
        parent_field = 'parent'

    def __str__(self):
        return f'{self.name}:{self.model}'


# 菜单的查询场景：1. 根据当前登录的用户得到它的权限和组权限。2. Filter菜单Permission in 用户的权限集或空。


def app_verbose_name(self):
    try:
        return apps.get_app_config(self.app_label).verbose_name
    except LookupError:
        return self.name


class ContentTypeGMeta:
    computed_fields = [
        {'name': 'app_verbose_name', 'display_name': '模块', 'type': FieldType.STRING}
    ]
    title_field = 'model'


setattr(ContentType, 'app_verbose_name', app_verbose_name)
setattr(ContentType, 'GMeta', ContentTypeGMeta)


def permissions_new_str(self):
    name = self.name
    if 'Can delete' in name:
        return name.replace('Can delete', '删除')
    elif 'Can add' in name:
        return name.replace('Can add', '添加')
    elif 'Can change' in name:
        return name.replace('Can change', '修改')
    elif 'Can view' in name:
        return name.replace('Can view', '查看')

    return "{} | {} | {}".format(
        self.content_type.app_verbose_name(), self.content_type, name
    )


@property
def display_name(self):
    name = self.name
    if 'Can delete' in name:
        return name.replace('Can delete', '删除')
    elif 'Can add' in name:
        return name.replace('Can add', '添加')
    elif 'Can change' in name:
        return name.replace('Can change', '修改')
    elif 'Can view' in name:
        return name.replace('Can view', '查看')
    else:
        return name


class PermissionGMeta:
    title_field = 'display_name'
    computed_fields = [
        {'name': 'display_name', 'display_name': '显示名称', 'type': FieldType.STRING}
    ]


Permission.__str__ = permissions_new_str
setattr(Permission, 'display_name', display_name)
setattr(Permission, 'GMeta', PermissionGMeta)


class Admin(models.Model):
    model = models.CharField('模型名称', max_length=100)
    config = JSONField(default={})

    class Meta:
        verbose_name = 'Admin配置'
        verbose_name_plural = 'Admin配置'

class Setting(models.Model):
    key = models.CharField('配置键', max_length=30, unique=True, blank=False)
    value = models.CharField('配置值', max_length=255, null=True, blank=False)
    type = models.CharField('键类型', max_length=30, default='string', choices=[
        ('string', '字符串'),
        ('text', '文本'),
        ('integer', '整型'),
        ('float', '浮点数'),
        ('decimal', '小数'),
        ('bool', 'Boolean值'),
        ('time', '时间'),
        ('date', '日期'),
        ('datetime', '日期时间'),
        ('image', '图片'),
        ('file', '文件'),
    ])
    display_name = models.CharField('中文名', max_length=30)


    class Meta:
        verbose_name = '网站配置'
        verbose_name_plural = '网站配置'

