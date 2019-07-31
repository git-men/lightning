from django.core.management.base import BaseCommand

from api_basebone.restful.client import views


def get_content_from_list(app, model_name, action):
    contentList = []
    contentList.append(
        f"| url          | /basebone/client/{app}__{model_name.lower()}/list/ |"
    )
    return '\n'.join(contentList)


class Command(BaseCommand):
    """输出模型配置

    只是简单的输出模型的配置，输出后的配置可进行调整和修改
    """

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help='指定导出api文档的app')

    def handle(self, *args, **kwargs):
        self.stdout.write('export actions api document...')
        app = kwargs.get('app')

        contentList = []
        contentList.append(f"# app：{app}")
        for key, data in views.exposed_apis.items():
            if not key.startswith(f'{app}__'):
                continue
            _, model_name = key.split('__')
            for action in data['actions']:
                if action == 'func':
                    continue
                contentList.append(f"## 模块：{model_name}<br/>————接口：{action}")

        api_file = f'{app}.md'
        try:
            print(f'-------------------开始导出 {app} api document ------------------')
            with open(api_file, 'w+', encoding='utf-8') as f:
                f.truncate()
                f.write('\n'.join(contentList))
            print(f'------------------- 导出 api document 结束 ----------------------')
        except Exception as e:
            print('导出 API document异常： {}'.format(str(e)))

