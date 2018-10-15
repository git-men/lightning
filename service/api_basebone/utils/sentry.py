from django.conf import settings
from raven import Client


class SentryClient(object):
    """
    Raven client

    用法:

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()
    """

    def __init__(self, *args, **kwargs):
        self._raven_client = None

    @property
    def client(self):
        """构建 client"""
        try:
            if self._raven_client is None:
                self._raven_client = Client(settings.RAVEN_CONFIG.get('dsn'))
            return self._raven_client
        except AttributeError:
            return


sentry_client = SentryClient().client
