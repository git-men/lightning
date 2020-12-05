from django.conf import settings as django_settings

DEFAULTS = {
    # 管理端是否使用日志记录器
    'MANAGE_USE_ACTION_LOG': True,
    'MANAGE_API_PERMISSION_VALIDATE_ENABLE': False,
    # 管理端操作数据时权限检测
    'MANAGE_GUARDIAN_DATA_PERMISSION_CHECK': False,
    # 管理端使用 guardian 检测的应用模型，元素数据格式为 {app_name}__{model_name}
    'MANAGE_GUARDIAN_DATA_APP_MODELS': [],
}


class BaseBoneSettings(object):
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = self.__check_user_settings(user_settings)
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(django_settings, 'BASEBONE_API_SERVICE', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.defaults[attr]

        self._cached_attrs.add(attr)
        setattr(self, attr, value)
        return value

    def __check_user_settings(self, user_settings):
        return user_settings


settings = BaseBoneSettings(None, DEFAULTS)
