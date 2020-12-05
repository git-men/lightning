from django.conf import settings

DEFAULT_WEBSITE_CONFIG = [
    {
        "permission_code":"can_web_setting",
        'title': "网站设置",
        'key': 'web_setting',
        "fields": [
            {"name": 'title', "type":"string", "displayName": '应用名', 'public':True},
            {"name":'logo', "type":"string", "displayName": 'LOGO', "widget": "ImageUploader", 'public':True},
        ]
    },
    {
        "permission_code":"can_gm_sms",
        'title': "短信配置",
        'key': 'gm_sms',
        "fields": [
            {"name":'gm_sdk_service_provider', "type":"string", "displayName": '供应商',
             'choices': [['tencent', '腾讯云'], ['aliyun', '阿里云']], 'widget': 'Radio'},

            # 腾讯
            {"name":'gm_sms_app_id', "type":"string", "displayName": '应用 ID',"show":'${gm_sdk_service_provider} ==="tencent"'},
            {"name":'gm_sms_app_key', "type":"string", "displayName": '应用 KEY',"show":'${gm_sdk_service_provider} ==="tencent"'},

            # 阿里
            {"name":'gm_sms_acs_access_key', "type":"string", "displayName": '应用 KEY',"show":'${gm_sdk_service_provider} ==="aliyun"'},
            {"name":'gm_sms_acs_access_secret', "type":"string", "displayName": '应用 SECRET',"show":'${gm_sdk_service_provider} ==="aliyun"'},
            {"name":'gm_sms_region', "type":"string", "displayName": '短信服务地区设置',"show":'${gm_sdk_service_provider} ==="aliyun"'},

            {"name":'gm_sms_app_template_id', "type":"string", "displayName": '应用模板 ID',},
            {"name":'gm_sms_app_sign', "type":"string", "displayName": '短信签名',},
            {"name":'gm_sms_live_minutes', "type":"integer", "displayName": '短信验证码有效期',"default": 5},
            {"name":'gm_sms_day_limit', "type":"integer", "displayName": '短信每天发送限制次数',"default": 3},


        ]
    },
    {
        'permission_code': 'can_config_email',
        'title': '邮件配置',
        'key': 'email',
        'fields': [
            {'name': 'mail_protocol', 'type': 'string', 'displayName': '类型', 'default': None, 'choices': [
                [None, '停用'], ['SMTP', 'SMTP'], ['SMTP_SSL', 'SMTP SSL加密'],
            ], 'widget': 'Radio'},
            {'name': 'mail_host', 'type': 'string', 'displayName': '邮件服务器', 'required': True},
            {'name': 'mail_port', 'type': 'integer', 'displayName': '端口号', 'help': '不填将会使用默认值', 'validators': [
                {'type': 'min_value', 'value': '0'}, {'type': 'max_value', 'value': '65535'},
            ]},
            {'name': 'mail_need_login', 'type': 'bool', 'displayName': '需要登录', 'default': True},
            {'name': 'mail_username', 'type': 'string', 'displayName': '用户名', 'required': True, 'show': '${mail_need_login}'},
            {'name': 'mail_password', 'type': 'string', 'displayName': '登录密码', 'show': '${mail_need_login}', 'widget': 'PasswordInput'},
            {'name': 'start_tls', 'type': 'bool', 'displayName': 'StartTLS加密'},
            {'name': 'sender_name', 'type': 'string', 'displayName': '发件人名字'},
            {'name': 'sender_address', 'type': 'string', 'displayName': '发件人邮箱', 'validators': [{'type': 'email'}]},
        ],
    },
    {
        "permission_code":"can_upload",
        'title': "上传配置",
        'key': 'upload',
        "fields": [
            {"name":'upload_provider', "type":"string", "displayName": '供应商', 'default': 'file_storage',
             'choices': [['file_storage', '文件系统'], ['oss', '阿里云'], ['cos', '腾讯云']],'widget': 'Radio'},

            {"name": 'storage_path', "type": "string", "displayName": '存储路径', "show": '${upload_provider} === "file_storage"', 'default': settings.MEDIA_ROOT or 'lightning-files'},

            {"name":'upload_dir', "type":"string", "displayName": '上传目录',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_key', "type":"string", "displayName": '访问密钥(Key)',"show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_secret', "type":"string", "displayName": 'Secret',"show":'${upload_provider} === "oss"'},
            # {"name":'ali_yun_oss_endpoint', "type":"string", "displayName": '上传域名', "help": "endpoint", "show":'${upload_provider} === "oss"'},
            # host、cdn_host、endpoint之间的关系混乱，而且前端只有host是生效的，暂时只保留host
            {"name":'ali_yun_oss_host', "type":"string", "displayName": '域名', "help": "用作上传和访问，可使用CDN", "show":'${upload_provider} === "oss"'},
            {"name":'ali_yun_oss_bucket', "type":"string", "displayName": '存储空间', "help": "bucket", "show":'${upload_provider} === "oss"'},

            {"name":'qcloud_appid', "type":"string", "displayName": 'APPID',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_secret_id', "type":"string", "displayName": 'SecretId',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_secret_key', "type":"string", "displayName": 'secretKey',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_bucket', "type":"string", "displayName": '存储空间',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_duration_seconds', "type":"integer", "displayName": '有效时间(秒)',"show":'${upload_provider} === "cos"'},
            {"name":'qcloud_cos_region', "type":"string", "displayName": '地域',"show":'${upload_provider} === "cos"'},
        ]
    },
]
