import os
import collections
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


class DataConvert:
    """数据转换器"""

    def string_handler(self, value):
        return value

    def integer_handler(self, value):
        return int(value)

    def handler(self, value, value_type):
        func = getattr(self, f'{value_type}_handler', None)
        if func:
            return func(value)
        return value


data_convert = DataConvert()


class SettingClient:
    """配置访问器"""

    BSM_CONFIG_APP = 'bsm_config'

    def __init__(self, *args, **kwargs):
        # 表明配置是否放在了数据库中
        self._use_db = self.BSM_CONFIG_APP in django_settings.INSTALLED_APPS

    def _get_config_from_settings(self, key):
        """从配置文件中获取对应的配置"""
        key = key.upper()
        try:
            return getattr(django_settings, key)
        except Exception:
            return os.environ.get(key)

    def __getattr__(self, key):
        if not self._use_db:
            return self._get_config_from_settings(key)

        key = key.lower()

        instance = Setting.objects.filter(key=key).first()
        if not instance:
            return self._get_config_from_settings(key)
        return instance.value


settings = SettingClient()


class SiteSetting:
    def __getitem__(self, item):
        if isinstance(item, collections.Iterable):
            setting_list = Setting.objects.filter(key__in=item).values_list('key', 'value')
            setting_dict = dict(setting_list)
            for i in item:
                yield setting_dict.get(i, None)
        else:
            setting = Setting.objects.filter(key=item).first()
            return setting and setting.value

    def __setitem__(self, key, value):
        setting = Setting.objects.filter(key=key).first()
        if setting:
            setting.value = value
            setting.save(update_fields=['value'])
        else:
            Setting.objects.create(key=key, value=value)


site_setting = SiteSetting()
