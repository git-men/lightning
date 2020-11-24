from django.core.management.base import BaseCommand, CommandError
from bsm_config.models import Menu, Admin

from lightning.services import generate_configs

class Command(BaseCommand):
    help = 'Generate lightning Menu and Admin pages'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        if not options['apps']:
            self.stdout.write(self.style.ERROR('app label is required for lighting generation'))
        generate_configs(options['apps'])
        self.stdout.write(self.style.SUCCESS('lightning admin config successfully generated!'))

