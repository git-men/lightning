import logging
from django.conf import settings

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as default_exception_handler, set_rollback

from ..core.exceptions import BusinessException, PARAMETER_FORMAT_ERROR
from ..utils.api_response import error_response
from ..utils.sentry import sentry_client


logger = logging.getLogger('django')


def business_exception_handler(exc, context):

    set_rollback()
    return error_response(exc.error_code, exc.error_message, exc.error_data)


def exception_handler(exc, context):
    """异常接收处理器"""

    if isinstance(exc, BusinessException):
        return business_exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return error_response(PARAMETER_FORMAT_ERROR, data=exc.detail)

    response = default_exception_handler(exc, context)
    if response:
        return response

    if not settings.DEBUG:
        # 记录错误日志到对应的日志处理器中
        logger = logging.getLogger('django')
        logger.exception(exc)

        try:
            # 如果有设置 sentry，日志打到对应的 sentry 中
            if sentry_client:
                sentry_client.captureException()
        except Exception:
            pass

        # 如果是非开发环境，则返回对应的错误，而不是直接报 500
        return business_exception_handler(
            BusinessException(error_data=str(exc)), context)
