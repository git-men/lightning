from api_basebone.utils.wechat.extension.logistics import WeChatLogistics
from api_basebone.utils.wechat import wrap

def create_logistics(app_id):
    return wrap(WeChatLogistics, app_id)
     

