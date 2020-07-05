from api_basebone.core.exceptions import BusinessException

GET_CONFIG_ERROR = '10000'

ERROR_PHRASES = {
    GET_CONFIG_ERROR: '获取配置异常',
}


def raise_business_exception(error_code, error_message=None, error_data=None):
    """抛出业务异常"""
    error_message = error_message if error_message else ERROR_PHRASES.get(error_code)
    raise BusinessException(
        error_code=error_code,
        error_message=error_message,
        error_data=error_data,
        error_app='bsm_config',
    )
