from django.apps import AppConfig


class ShieldConfig(AppConfig):
    name = 'shield'

    def ready(self):
        from . import filter, signals
