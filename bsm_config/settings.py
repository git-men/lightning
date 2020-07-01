from django.conf import settings as django_settings
from .models import Setting

"""
环境变量中的 KEY 和 数据库中配置 KEY 的映射

规则：
    - 数据库中的配置是 settings 键的大写或者小写

当查配置时，根据是否使用了数据库配置的开关，进行配置的查询，如果键在数据库中存在，则直接获取值

如果不存在，则把键转换为大写，然后从 settings 中获取对应的配置
"""
# 钉钉移动接入应用登陆应用 key
DINGDING_FLEXIBLE_LOGIN_APP_KEY = 'dingding_flexible_login_app_key'
# 钉钉移动接入应用登陆应用 secret
DINGDING_FLEXIBLE_LOGIN_APP_SECRET = 'dingding_flexible_login_app_secret'
# 钉钉企业内部开发 H5 微应用 KEY
DINGDING_ENTERPRISE_INNER_H5_APP_KEY = 'dingding_enterprise_inner_h5_app_key'
# 钉钉企业内部开发 H5 微应用 SECRET
DINGDING_ENTERPRISE_INNER_H5_APP_SECRET = 'dingding_enterprise_inner_h5_app_secret'
# 钉钉企业唯一标识符
DINGDING_CORP_ID = 'dingding_corp_id'


class SettingClient:
    """配置访问器"""

    BSM_CONFIG_APP = 'bsm_config'

    def __init__(self, *args, **kwargs):
        # 表明配置是否放在了数据库中
        self._use_db = self.BSM_CONFIG_APP in django_settings.INSTALLED_APPS

    def _get_config_from_settings(self, key):
        """从配置文件中获取对应的配置"""
        return getattr(django_settings, key.upper())

    def __getattr__(self, key):
        if not self._use_db:
            return self._get_config_from_settings(key)

        key = key.lower()

        instance = Setting.objects.filter(key=key).first()
        if not instance:
            return self._get_config_from_settings(key)
        return instance.value


settings = SettingClient()
