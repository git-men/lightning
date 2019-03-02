import arrow
from django.conf import settings


def camel_to_underline(camel_format):
    """驼峰命名格式转下划线命名格式"""

    underline_format = ''
    if isinstance(camel_format, str):
        for _s_ in camel_format:
            underline_format += _s_ if _s_.islower() else '_'+_s_.lower()
    return underline_format


def first_lower(data):
    if data:
        return data[:1].lower() + data[1:]
    return ''


def underline_to_camel(underline_format):
    """下划线命名格式驼峰命名格式
    """
    camel_format = ''
    if isinstance(underline_format, str):
        for item in underline_format.split('_'):
            camel_format += item.capitalize()
    return first_lower(camel_format)


def format_human_datetime(value):
    """格式化时间"""
    if not value:
        return ''

    return arrow.get(value).to(settings.TIME_ZONE).format(
        'YYYY-MM-DD HH:mm:ss'
    )
