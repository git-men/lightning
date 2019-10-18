PARAM_USER_ID = 'user_id'
PARAM_USER_NICK_NAME = 'user_nick_name'
PARAM_TRUE = 'true'
PARAM_FALSE = 'false'
PARAM_NULL = 'null'

API_SERVER_PARAM = {
    PARAM_USER_ID: lambda request: request.user.id,
    PARAM_USER_NICK_NAME: lambda request: request.user.nick_name,
    PARAM_TRUE: lambda request: True,
    PARAM_FALSE: lambda request: False,
    PARAM_NULL: lambda request: None,
}

