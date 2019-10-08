from django.apps import AppConfig


class ApiBaseboneConfig(AppConfig):
    name = 'api_basebone'

    def ready(self):
        # import member.bsm.functions.form_id
        # from member import signals
        from api_basebone.restful.client.views import register_api
        from api_basebone.bsm.api import exposed
        import api_basebone.bsm.functions  # 注册所有云函数

        register_api(self.name, exposed)

        import api_basebone.api_config
