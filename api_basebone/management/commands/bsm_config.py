import os
import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from api_basebone.export.fields import get_app_field_schema
from api_basebone.export.admin import get_app_admin_config


class Command(BaseCommand):
    """输出模型配置

    只是简单的输出模型的配置，输出后的配置可进行调整和修改
    """

    ADMIN_TEMPLATE = 'bsm_admin_config.html'
    SCHEMA_TEMPLATE = 'bsm_schema_config.html'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action', type=str, default='all',
            choices=['admin', 'schema', 'all'],
            help='指定导出配置的类型, 可选 admin schema, all'
        )

    def _get_host(self):
        """获取请求服务地址"""
        default_host = 'http://127.0.0.1:8000'
        return getattr(settings, 'BSM_EXPORT_SERVICE_HOST', default_host)

    def _get_admin_config(self, action):
        """导出 admin 配置"""
        if action not in ['all', 'admin']:
            return

        try:
            print('-------------------开始导出 admin 配置------------------')
            host = self._get_host()
            url = os.path.join(host, 'basebone/config/admin/')
            data = requests.get(url).json()
            content = render_to_string(self.ADMIN_TEMPLATE, data)
            admin_file = os.path.join(settings.FRONT_END_PROJECT_PATH, 'src/admin/index.js')
            with open(admin_file, 'r+') as f:
                f.truncate()
                f.write(content)
            print('-------------------开始导出 admin 配置成功结束------------------')
        except Exception as e:
            print('导出 admin 配置异常 {}'.format(str(e)))

    def _get_schema_config(self, action):
        """导出 schema 配置"""

        if action not in ['schema', 'all']:
            return

        try:
            print('-------------------开始导出 schema 配置------------------')
            host = self._get_host()
            url = os.path.join(host, 'basebone/config/schema/')
            data = requests.get(url).json()
            content = render_to_string(self.SCHEMA_TEMPLATE, data)

            schema_file = os.path.join(settings.FRONT_END_PROJECT_PATH, 'src/schemas/config.json')
            with open(schema_file, 'r+') as f:
                f.truncate()
                f.write(content)
            print('-------------------开始导出 schema 配置成功结束------------------')
        except Exception as e:
            print('导出 schema 配置异常 {}'.format(str(e)))

    def handle(self, *args, **kwargs):
        self.stdout.write('hello export model admin config...')
        action = kwargs.get('action')

        self._get_admin_config(action)
        self._get_schema_config(action)
