import json
import logging
import traceback
from django.conf import settings
from django.apps import apps

from django.core.management.base import BaseCommand
from api_basebone.api.driver import db

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """输出模型配置

    只是简单的输出模型的配置，输出后的配置可进行调整和修改
    """

    def add_arguments(self, parser):
        """"""
        parser.add_argument('--app', type=str, help='导出api的app')

    def handle(self, *args, **kwargs):
        """"""
        self.stdout.write('导出 api 配置...')
        app = kwargs.get('app')
        if app:
            export_apps = [app]
        else:
            export_apps = getattr(settings, 'BSM_EXPORT_APPS', None) + getattr(
                settings, 'INTERNAL_APPS', None
            )
            export_apps = list(set(export_apps))

        error_list = []
        success_list = []
        for app in export_apps:
            f = None
            try:
                app_config = apps.get_app_config(app)
                path = app_config.module.__path__[0] + '/api_config.json'
                api_list = db.list_api_config(app)
                if not api_list:
                    continue
                print(f'-------------------开始导出 app：{app} 的api配置 ------------------')
                api_config_list = []
                for api_config in api_list:
                    api_config_list.append(api_config)

                api_json = json.dumps(
                    api_config_list, ensure_ascii=False, indent=4, sort_keys=True
                )
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(api_json)
                    success_list.append(app)
                print(f'------------------- 导出 api 配置完成 ----------------------------')
            except Exception as e:
                error_list.append(app)
                print('导出 API 异常： {}'.format(traceback.format_exc()))

        print(f'api导出成功')
        print(f'成功的app：{success_list}')
        print(f'失败的app：{error_list}')
        # print(f'{success_num}个API导出成功，{change_num}个变更，{error_num}个API 异常')
