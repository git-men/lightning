SETTINGS_CONFIG = [
    {
        "permission_code":"can_web_setting",
        'title': "网站设置",
        'key': 'web_setting',
        "fields": [
            {"name": 'title', "type":"string", "displayName": '应用名', 'public':True},
            {"name":'logo', "type":"string", "displayName": 'LOGO', "weiget": "Image", 'public':True},
            {"name":'ls', "type":"text", "displayName": 'License', 'public':True, "required": True, 'widget': 'License',},
        ]
    },
    {
        "permission_code":"can_custom_staff",
        'title': "自定义用户",
        'key': 'custom_staff',
        "fields": [
            {"name":'staff_model', "type":"string", "displayName": '员工表', 'public':True, "options": {"models": ['user_app'],}, "widget": 'ModelSelect'},
            {"name":'staff_username', "type":"string", "displayName": '员工登录字段', 'public':True, "options": {"schemas": 'SCHEMAS', "model": '${staff_model}',}, "widget": 'FieldSelect'},
            {"name":'staff_active', "type":"string", "displayName": '员工状态字段', 'help': '必须是唯一的字段', 'public':True, "options": {"schemas": 'SCHEMAS',  "model": '${staff_model}',},"widget": 'FieldSelect' }, 
        ]
    },
    {
        "permission_code": "can_other_login",
        'title': "第三方登录接入配置",
        'key': 'other_login',
        'help_text':'企业微信和钉钉只可接入一个,保存后不可更改',
        "fields":[
            {
                "name":'third_party_provider', "type":"string", "displayName": '接入第三方平台', 
                'choices': [['false', '不接入'], ['wechat', '企业微信'], ['dingding', '钉钉']],
                'widget': 'Radio', 'public':True
            },

            {"name": "wechat_work_appid", "type":'string', "displayName": '企业微信公司ID', "required": True,"show":'${third_party_provider} === "wechat"'},
            {"name": "wechat_work_agentid", "type":'string', "displayName": '企业微信应用ID', "required": True,"show":'${third_party_provider} === "wechat"'}, 
            {"name": "wechat_work_redirect_uri",  "type":'string', "displayName": '登录回调域名', "required": True,"show":'${third_party_provider} === "wechat"'},
            {"name": "wechat_work_app_secret", "type":'string', "displayName": '企业微信应用密匙', "required": True,"show":'${third_party_provider} === "wechat"'},
            {"name": "dingding_flexible_login_app_key", "type":'string', "displayName": '登陆应用 key', "required": True,"show":'${third_party_provider} ==="dingding"'},

            {"name": "dingding_flexible_login_app_secret", "type":'string', "displayName": '登陆应用 secret', "required": True,"show":'${third_party_provider} ==="dingding"'},
            {"name": "dingding_flexible_login_redirect_uri", "type":'string', "displayName": '登陆应用 redirect_uri', "required": True,"show":'${third_party_provider} ==="dingding"'},
            {"name": "dingding_enterprise_inner_h5_app_key", "type":'string', "displayName": 'H5 微应用 KEY', "required": True,"show":'${third_party_provider} ==="dingding"'},
            {"name": "dingding_enterprise_inner_h5_app_secret", "type":'string', "displayName": 'H5 微应用 SECRET', "required": True, "show":'${third_party_provider} ==="dingding"'},
            {"name": "dingding_corp_id", "type":'string', "displayName": '唯一标识符', "required": True, "show":'${third_party_provider} ==="dingding"'},
        ]
    },
    {
        "permission_code":"can_gm_sms",
        'title': "短信配置",
        'key': 'gm_sms',
        "fields": [
            {"name":'gm_sdk_service_provider', "type":"string", "displayName": '供应商', 
            'choices': [['tencent', '腾讯云'], ['aliyun', '阿里云']], 'widget': 'Radio'},
            {"name":'gm_sms_app_id', "type":"string", "displayName": '应用 ID',},
            {"name":'gm_sms_app_key', "type":"string", "displayName": '应用 KEY',}, 
            {"name":'gm_sms_app_template_id', "type":"string", "displayName": '应用模板 ID',}, 
            {"name":'gm_sms_app_sign', "type":"string", "displayName": '短信签名',}, 
            {"name":'gm_sms_live_minutes', "type":"string", "displayName": '短信验证码有效期',}, 
            {"name":'gm_sms_day_limit', "type":"integer", "displayName": '短信每天发送限制次数',}, 
            {"name":'gm_sms_region', "type":"string", "displayName": '短信服务地区设置',}, 
        ]
    },
    {
        "permission_code":"can_upload",
        'title': "上传配置",
        'key': 'upload',
        "fields": [
            {"name":'upload_provider', "type":"string", "displayName": '供应商', 
            'choices': [['oss', '阿里云'], ['cos', '腾讯云']],'widget': 'Radio'},
            
            {"name":'upload_dir', "type":"string", "displayName": '上传目录',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_key', "type":"string", "displayName": '访问密钥(Key)',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_secret', "type":"string", "displayName": 'Secret',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_endpoint', "type":"string", "displayName": '访问域名',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_host', "type":"string", "displayName": '上传域名',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_bucket', "type":"string", "displayName": '存储空间',"show":'${upload_provider} === "oss"'},

            {"name":'qcloud_appid', "type":"string", "displayName": 'APPID',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_secret_id', "type":"string", "displayName": 'SecretId',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_secret_key', "type":"string", "displayName": 'secretKey',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_bucket', "type":"string", "displayName": '存储空间',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_duration_seconds', "type":"integer", "displayName": '有效时间(秒)',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_region', "type":"string", "displayName": '地域',"show":'${upload_provider} === "cos"'},
        ]
    },
]