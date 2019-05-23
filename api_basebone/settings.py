from django.conf import settings as django_settings

DEFAULTS = {
    # 管理端是否使用日志记录器
    'MANAGE_USE_ACTION_LOG': True
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
