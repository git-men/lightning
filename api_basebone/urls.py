from django.urls import path, include

app_name = 'basebone_common'

urlpatterns = [

    # 通用管理端
    path(
        'basebone/<str:app>__<str:model>/',
        include(
            ('api_basebone.restful.manage.urls', app_name),
            namespace='manage.common.basebone'
        )
    ),

    # 通用客户端
    path(
        'basebone/client/<str:app>__<str:model>/',
        include(
            ('api_basebone.restful.client.urls', app_name),
            namespace='client.common.basebone'
        )
    ),

    # 配置输出
    path(
        'basebone/config/',
        include(
            ('api_basebone.restful.manage.config_urls', app_name),
            namespace='schema.config'
        )
    ),

    # 通用 app 管理端
    path(
        'basebone/manage/',
        include(
            ('api_basebone.app.manage_urls', app_name),
            namespace='manage.app.basebone'
        )
    ),
]
