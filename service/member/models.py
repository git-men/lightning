from django.contrib.auth.models import AbstractUser
from django.db import models


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

    class Meta:
        verbose_name = '作者'
        verbose_name_plural = '作者'

    def __str__(self):
        return self.username
