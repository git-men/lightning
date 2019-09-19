PARAM_USER_ID = 'user_id'
PARAM_USER_NICK_NAME = 'user_nick_name'

API_SERVER_PARAM = {
    PARAM_USER_ID: lambda request: request.user.id,
    PARAM_USER_NICK_NAME: lambda request: request.user.nick_name,
}

