from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """输出模型配置

    只是简单的输出模型的配置，输出后的配置可进行调整和修改
    """

    def handle(self, *args, **kwargs):
        self.stdout.write('hello export model config...')
