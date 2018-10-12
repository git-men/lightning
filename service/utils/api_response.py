
from rest_framework.response import Response

from utils.exceptions import ERROR_PHRASES


def success_response(obj=None, http_rsp=False):
    if obj is not None:
        rsp_data = {'error_code': '0', 'error_message': '', 'result': obj}
    else:
        rsp_data = {'error_code': '0', 'error_message': ''}

    return Response(rsp_data)


def error_response(code, message=None, data=None):
    if not message:
        message = ERROR_PHRASES.get(code, '')

    if data:
        response_data = {'error_code': code, 'error_message': message, 'error_data': data}
    else:
        response_data = {'error_code': code, 'error_message': message}

    return Response(response_data, status=HTTP_400_BAD_REQUEST)
