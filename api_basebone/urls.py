from django.urls import path, include

app_name = 'basebone_common'

urlpatterns = [

    # 通用管理端
    path(
        'basebone/<str:app>__<str:model>/',
        include(
            ('api_basebone.basebone_urls', app_name),
            namespace='manage.common.basebone'
        )
    ),

    # 配置输出
    path(
        'basebone/config/',
        include(
            ('api_basebone.urls_config', app_name),
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
