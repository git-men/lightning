from django.conf import settings
from django.contrib.auth import get_user_model
# 暂不支持菜单组,嵌套子菜单
User = get_user_model()

DEFAULT_MENU = [
        # {"name":"仪表盘","children":[],"model":None,"page":"chart","icon":"line-chart"},
        {  
            "name":"权限管理",
            "model":"",
            "type": "group",
            "icon":"lock",
            "children":[
                {"name":"账号管理","children":[],"model":f"{User._meta.app_label}__{User._meta.model_name}","page":"list","icon":""},
                {"name":"角色管理","children":[],"model":"auth__group","page":"list","icon":""},
                {"name":"资源权限","children":[],"model":"auth__permission","page":"list","icon":""},
            ]
        },
        {
            "name":"开发管理",
            "model":"",
            "type": "group",
            "icon":"tool",
             "children":[
                {"name":"菜单管理","children":[],"model":"bsm_config__menu","page":"list","icon":"menu",},
                {"name":"页面配置","children":[],"model":"","page":"adminConfig","icon":"block__outlined",},
                # {"name":"API管理","children":[],"model":"api_db__api","page":"list","icon":"api"},
                # {"name":"触发器管理","children":[],"model":"trigger_core__trigger","page":"list","icon":"fork"},    
            ]
        }
]
