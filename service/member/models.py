from django.contrib.auth.models import AbstractUser
from django.db import models


class Ship(models.Model):
    
    name = models.CharField('名称', max_length=20)
    title = models.CharField('标题', max_length=20, blank=True, default='')

    class Meta:
        verbose_name = '船'
        verbose_name_plural = '船'

    def __str__(self):
        return self.name


class Author(AbstractUser):
    GENDER_CHOICES = (
        (0, '女'),
        (1, '男'),
    )

    age = models.IntegerField('年龄', null=False, default=0)
    name = models.CharField('名称', max_length=20, default='无')
    city = models.CharField('城市', max_length=20, blank=True, default='')
    gender = models.PositiveIntegerField(
        '性别', choices=GENDER_CHOICES, default=1)
    ship = models.ForeignKey(Ship, verbose_name='船', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = '作者'
        verbose_name_plural = '作者'

    def __str__(self):
        return self.username
