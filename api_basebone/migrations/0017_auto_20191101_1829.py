# Generated by Django 2.1.3 on 2019-11-01 10:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_basebone', '0016_auto_20191022_1928'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='displayfield',
            name='api',
        ),
        migrations.RemoveField(
            model_name='filter',
            name='api',
        ),
        migrations.RemoveField(
            model_name='filter',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='parameter',
            name='api',
        ),
        migrations.RemoveField(
            model_name='parameter',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='setfield',
            name='api',
        ),
        migrations.DeleteModel(
            name='Api',
        ),
        migrations.DeleteModel(
            name='DisplayField',
        ),
        migrations.DeleteModel(
            name='Filter',
        ),
        migrations.DeleteModel(
            name='Parameter',
        ),
        migrations.DeleteModel(
            name='SetField',
        ),
    ]