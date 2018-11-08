import arrow

from django.conf import settings


def local_timestamp():
    return arrow.utcnow().to(settings.TIME_ZONE).timestamp


def timestamp_serializer(timestamp):
    return arrow.get(timestamp).to(settings.TIME_ZONE).format('YYYY-MM-DD HH:mm:ss')
