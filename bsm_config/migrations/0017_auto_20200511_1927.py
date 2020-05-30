# Generated by Django 2.2.9 on 2020-05-11 11:27

from django.db import migrations, models

def update_menu_type(apps, schema_editor):
    print('更新有children的菜单类型为菜单组')
    Menu = apps.get_app_config('bsm_config').get_model('Menu')
    Menu.objects.filter(children__isnull=False).update(type='group')

class Migration(migrations.Migration):

    dependencies = [
        ('bsm_config', '0016_auto_20200429_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='type',
            field=models.CharField(choices=[('item', '菜单项'), ('group', '菜单组')], default='item', max_length=20, verbose_name='菜单类型'),
        ),
        migrations.AlterField(
            model_name='menu',
            name='icon',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='图标'),
        ),
        migrations.AlterField(
            model_name='menu',
            name='model',
            field=models.CharField(max_length=200, null=True, verbose_name='关联模型'),
        ),
        migrations.AlterField(
            model_name='menu',
            name='name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='名称'),
        ),
        migrations.AlterField(
            model_name='menu',
            name='page',
            field=models.CharField(choices=[['list', '列表页'], ['detail', '详情页'], ['adminConfig', '页面配置面板'], ['auto', '自定义页面'], ['chart', '自定义图表']], default='', help_text='前端功能页面的标识', max_length=200, null=True, verbose_name='页面'),
        ),
        migrations.RunPython(update_menu_type, reverse_code=migrations.RunPython.noop)
    ]
