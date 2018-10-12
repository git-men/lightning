import logging

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as default_exception_handler, set_rollback

from utils.api_response import error_response
from utils.exceptions import BusinessException, PARAMETER_FORMAT_ERROR


def business_exception_handler(exc, context):

    set_rollback()
    return error_response(exc.error_code, exc.error_message, exc.error_data)


def exception_handler(exc, context):

    if isinstance(exc, BusinessException):
        return business_exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return error_response(PARAMETER_FORMAT_ERROR, data=exc.detail)

    response = default_exception_handler(exc, context)
    if response:
        return response

    # return business_exception_handler(
    #     BusinessException(error_data=str(exc)), context)
