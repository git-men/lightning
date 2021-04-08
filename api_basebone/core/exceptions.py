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
MODEL_EXPORT_IS_NOT_SUPPORT = '10011'
BSM_NOT_STATISTICS_CONFIG = '10012'
BSM_CAN_NOT_FIND_ADMIN = '10013'
USER_NOT_HAVE_ENOUGH_PERM = '10014'
CAN_NOT_SAVE_API = '10015'
INVALID_API = '10016'
DISABLE_API = '10017'
SLUG_EXISTS = '10018'

CAN_NOT_SAVE_TRIGGER = '10019'
INVALID_TRIGGER = '10020'
DISABLE_TRIGGER = '10021'
TRIGGER_ERROR = '10022'

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
    MODEL_EXPORT_IS_NOT_SUPPORT: '指定的模型不支持导出',
    BSM_NOT_STATISTICS_CONFIG: '没有配置任何统计配置',
    BSM_CAN_NOT_FIND_ADMIN: '没有找到模型对应的 admin 模块',
    USER_NOT_HAVE_ENOUGH_PERM: '此模型用户没有权限进行操作',
    CAN_NOT_SAVE_API: '当前模式不支持API在线编辑',
    INVALID_API: '无此api',
    DISABLE_API: 'api已停用',
    SLUG_EXISTS: '标识已存在',
    CAN_NOT_SAVE_TRIGGER: '当前模式不支持触发器在线编辑',
    INVALID_TRIGGER: '无此触发器',
    TRIGGER_ERROR: '触发器运行异常',
}


class BusinessException(Exception):
    """通用业务异常类

    此类包含：
    - 参数格式错误
    - 服务异常错误
    - 业务错误
    """

    default_error_code = '9000'
    default_error_message = '系统错误'
    default_error_app = ''

    def __init__(self, error_code=None, error_message=None, error_data='', error_app='', logs=None):

        self.error_code = (
            error_code if error_code is not None else self.default_error_code
        )

        if error_message is not None:
            self.error_message = error_message
        else:
            get_message = ''
            if error_code in ERROR_PHRASES:
                get_message = force_text(ERROR_PHRASES.get(error_code))
            if not get_message:
                get_message = force_text(self.default_error_message)
            self.error_message = get_message

        self.error_data = error_data
        self.error_app = error_app if error_app else force_text(self.default_error_app)
        self.logs = logs

    def __str__(self):
        return f'error_code: {self.error_code}, error_message: {self.error_message}, error_data: {self.error_data}'
