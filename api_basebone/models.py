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
