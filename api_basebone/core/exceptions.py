from django.utils.encoding import force_text

PARAMETER_FORMAT_ERROR = '10000'
SERVER_IS_BUSY = '10001'
REQUEST_FORBIDDEN = '10002'
PARAMETER_BUSINESS_ERROR = '11000'
INVALID_TIME_RANGE = '10003'
OBJECT_NOT_FOUND = '10004'
APP_LABEL_IS_INVALID = '10005'
MODEL_SLUG_IS_INVALID = '10006'
CANT_NOT_GET_MODEL = '10007'
BATCH_ACTION_HAND_ERROR = '10008'
FUNCTION_NOT_FOUNT = '10009'
THIS_ACTION_IS_NOT_AUTHENTICATE = '10010'

ERROR_PHRASES = {
    PARAMETER_FORMAT_ERROR: '参数格式错误',
    SERVER_IS_BUSY: '服务器繁忙，请稍后再试',
    REQUEST_FORBIDDEN: '您没有执行该操作的权限',
    INVALID_TIME_RANGE: '结束时间不可早于开始时间',
    PARAMETER_BUSINESS_ERROR: '参数业务错误',
    OBJECT_NOT_FOUND: '找不到数据',
    APP_LABEL_IS_INVALID: '路由中指定的 app 不合法',
    MODEL_SLUG_IS_INVALID: '路由中指定的 model 不合法',
    CANT_NOT_GET_MODEL: '获取不到指定的模型',
    BATCH_ACTION_HAND_ERROR: '批量操作执行错误',
    FUNCTION_NOT_FOUNT: '找到不指定云函数',
    THIS_ACTION_IS_NOT_AUTHENTICATE: '此种请求不允许访问',
}


class BusinessException(Exception):
    """通用业务异常类

    此类包含：
    - 参数格式错误
    - 服务异常错误
    - 业务错误
    """

    default_error_code = "9000"
    default_error_message = "系统错误"

    def __init__(self, error_code=None, error_message=None, error_data=None):

        if error_code is not None and error_message is not None:
            self.error_code = error_code
            self.error_message = error_message
        elif error_code is not None:
            self.error_code = error_code
            self.error_message = force_text(ERROR_PHRASES.get(error_code))
        else:
            self.error_code = self.default_error_code
            self.error_message = force_text(self.default_error_message)
        self.error_data = error_data

    def __str__(self):
        return f'{self.error_code}:{self.error_message}'
