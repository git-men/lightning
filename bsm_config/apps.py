from django.apps import AppConfig
from django.db.models.signals import post_migrate


class BsmConfigConfig(AppConfig):
    name = 'bsm_config'
    verbose_name = '系统配置'
    
    def ready(self):
        from bsm_config.bsm import functions
        from bsm_config import signals
        from api_basebone.restful.client.views import register_api
        register_api('auth', {
            'permission': {
                'actions': ['retrieve', 'list', 'set']
            }
        })

        post_migrate.connect(signals.update_setting_config_permission, sender=self)