from django.urls import path, include

app_name = 'basebone_app'

urlpatterns = [
    path(
        'basebone/manage/',
        include(
            ('api_basebone.app.manage_urls', app_name),
            namespace='manage.common.basebone'
        )
    ),
]
