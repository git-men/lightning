from django.core.signals import request_finished
from django.dispatch import receiver
from rest_framework.response import Response

from api_basebone.core.exceptions import ERROR_PHRASES
from api_basebone.sandbox.logger import LogCollector
from werkzeug import Local

request_logs = Local()

@receiver(request_finished, dispatch_uid='clean_request_locals')
def clean_local(sender, **kwargs):
    if hasattr(request_logs, 'logger'):
        del request_logs.logger

def get_or_create_logger(name, log_type='function'):
    """如果无Logger则会创建
    """
    logger = getattr(request_logs, 'logger', None)
    if not logger:
        request_logs.logger = LogCollector(name, log_type)
    return request_logs.logger

def success_response(data=None):
    """成功返回的数据结构"""
    logger = getattr(request_logs, 'logger', None)
    if data is not None:
        response_data = {
            'error_code': '0',
            'error_message': '',
            'result': data,
            'logs': logger.collect() if logger else []
        }
    else:
        response_data = {
            'error_code': '0',
            'error_message': '',
            'logs': logger.collect() if logger else []
        }
    return Response(response_data)


def error_response(error_code, error_message=None, error_data=None, error_app=None, logs=None):
    """业务异常返回的数据结构"""
    logger = getattr(request_logs, 'logger', None)
    origin_logs = logger.collect() if logger else []
    if not error_message:
        error_message = ERROR_PHRASES.get(error_code, '')

    response_data = {
        'error_code': error_code,
        'error_message': error_message,
        'error_data': error_data,
        'error_app': error_app,
        'logs': origin_logs + (logs or [])
    }
    return Response(response_data)
