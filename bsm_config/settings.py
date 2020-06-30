from django.conf import settings
from .models import Setting

"""
环境变量中的 KEY 和 数据库中配置 KEY 的映射

规则：
    - 数据库中的配置是 settings 键的大写或者小写

当查配置时，根据是否使用了数据库配置的开关，进行配置的查询，如果键在数据库中存在，则直接获取值

如果不存在，则把键转换为大写，然后从 settings 中获取对应的配置
"""
DINGDING_APP_KEY = 'dingding_app_key'
DINGDING_APP_SECRET = 'dingding_app_secret'


# 可以在数据库中配置的列表
DB_KEY_LIST = [DINGDING_APP_KEY, DINGDING_APP_SECRET]


class SettingClient:
    """配置访问器"""

    BSM_CONFIG_APP = 'bsm_config'

    def __init__(self, *args, **kwargs):
        # 表明配置是否放在了数据库中
        self._use_db = self.BSM_CONFIG_APP in settings.INSTALLED_APPS

    def _get_config_from_settings(self, key):
        """从配置文件中获取对应的配置"""
        return getattr(settings, key.upper())

    def get_config(self, key):
        if not self._use_db:
            return self._get_config_from_settings(key)

        instance = Setting.objects.filter(key=key).first()
        if not instance:
            return self._get_config_from_settings(key)
        return instance.value


settings_client = SettingClient()
