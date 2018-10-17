
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from ..core.exceptions import ERROR_PHRASES


def success_response(data=None):
    """成功返回的数据结构"""

    if data is not None:
        response_data = {
            'error_code': '0',
            'error_message': '',
            'result': data,
        }
    else:
        response_data = {
            'error_code': '0',
            'error_message': '',
        }

    return Response(response_data)


def error_response(error_code, error_message=None, error_data=None):
    """业务异常返回的数据结构"""

    if not error_message:
        error_message = ERROR_PHRASES.get(error_code, '')

    if error_data:
        response_data = {
            'error_code': error_code,
            'error_message': error_message,
            'error_data': error_data
        }
    else:
        response_data = {
            'error_code': error_code,
            'error_message': error_message,
        }

    return Response(response_data)
