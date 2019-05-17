from django.apps import AppConfig


class BsmConfigConfig(AppConfig):
    name = 'bsm_config'
    verbose_name = '系统配置'
    
    def ready(self):
        from api_basebone.restful.client.views import register_api
        register_api('auth', {
            'permission': {
                'actions': ['retrieve', 'list', 'set']
            }
        })