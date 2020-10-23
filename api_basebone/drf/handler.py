import logging
import sys

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404

from rest_framework.exceptions import ValidationError, APIException
from rest_framework.views import set_rollback

from .response import error_response
from ..core.exceptions import BusinessException, PARAMETER_FORMAT_ERROR
from ..utils.sentry import sentry_client


logger = logging.getLogger('django')


def business_exception_handler(exc, context):

    set_rollback()
    return error_response(
        exc.error_code, exc.error_message, exc.error_data, exc.error_app)


def exception_handler(exc, context):
    """异常接收处理器"""
    if settings.DEBUG:
        import traceback
        t, v, tb = sys.exc_info()
        traceback.print_tb(tb)
    if isinstance(exc, BusinessException):
        logger.info(exc.error_message)
        return business_exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return error_response(
            PARAMETER_FORMAT_ERROR,
            error_data=exc.detail,
            error_app=getattr(exc, 'error_app', None)
        )

    if isinstance(exc, Http404):
        api_exception = BusinessException(
            error_code=404,
            error_message='找不到对应的数据详情'
        )
        return business_exception_handler(api_exception, context)

    if isinstance(exc, PermissionDenied):
        api_exception = BusinessException(
            error_code=403,
            error_message='当前用户的权限不够'
        )
        return business_exception_handler(api_exception, context)

    if isinstance(exc, APIException):
        api_exception = BusinessException(
            error_code=exc.status_code,
            error_message=exc.default_detail
        )
        return business_exception_handler(api_exception, context)

    if not settings.DEBUG:
        import traceback
        t, v, tb = sys.exc_info()
        traceback.print_tb(tb)

    logger.exception(exc)

    # 可自由配置是否直接抛出严重的错误
    CLOSE_DIRECT_SERIOUS_ERROR_SHOW = getattr(
        settings, 'CLOSE_DIRECT_SERIOUS_ERROR_SHOW', True)

    if CLOSE_DIRECT_SERIOUS_ERROR_SHOW:
        try:
            # 如果有设置 sentry，日志打到对应的 sentry 中
            sentry_client.captureException()
        except Exception:
            pass

        # 如果是非开发环境，则返回对应的错误，而不是直接报 500
        return business_exception_handler(
            BusinessException(error_data=str(exc)), context)
