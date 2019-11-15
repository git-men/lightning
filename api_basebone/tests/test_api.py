from django.test import TestCase, Client
from member.models import User

from api_basebone.core import exceptions
from api_core.services import api_services


class ApiTestCase(TestCase):
    def setUp(self):
        super().setUp()

        user = User(
            username='api_test',
            is_superuser=True,
            is_active=True,
            is_staff=True,
            email='',
            first_name='gitmen',
            last_name='gz',
        )
        user.set_password('1234@Temp')
        user.save()
        self.user = user

        self.client = Client()
        self.client.login(username='api_test', password='1234@Temp')

    def test_save(self):
        # 不给函数名
        data = {
            "func_name": "api_save",
            "params": {
                "config": {
                    "slug": "show_api",
                    "app": "api_db",
                    "model": "api",
                    "operation": "xxxxxx",
                }
            },
        }
        result = self.client.post(
            '/basebone/client/api_db__api/func/',
            data=data,
            content_type='application/json',
        ).json()
        self.assertEqual(exceptions.PARAMETER_FORMAT_ERROR, result['error_code'])

        config = {
            "slug": "show_api",
            "app": "api_db",
            "model": "api",
            "operation": "xxxxxx",
        }

        with self.assertRaisesMessage(
            exceptions.BusinessException, exceptions.PARAMETER_FORMAT_ERROR
        ):
            api_services.save_api(config)

    def test_func(self):
        # 不给函数名
        data = {
            "func_name": "api_save",
            "params": {
                "config": {
                    "slug": "show_api",
                    "app": "api_db",
                    "model": "api",
                    "operation": "func",
                }
            },
        }
        result = self.client.post(
            '/basebone/client/api_db__api/func/',
            data=data,
            content_type='application/json',
        ).json()
        self.assertEqual(exceptions.PARAMETER_FORMAT_ERROR, result['error_code'])

        # 保存云函数定义
        data = {
            "func_name": "api_save",
            "params": {
                "config": {
                    "slug": "show_api",
                    "app": "api_db",
                    "model": "api",
                    "operation": "func",
                    "func_name": "show_api",
                    "parameter": [
                        {"name": "slug", "type": "string", "required": True, "desc": ""}
                    ],
                }
            },
        }
        result = self.client.post(
            '/basebone/client/api_db__api/func/',
            data=data,
            content_type='application/json',
        ).json()
        self.assertEqual('0', result['error_code'])

        # 运行云函数api，不给参数
        data = {}
        result = self.client.post('/api/show_api/', data=data).json()
        self.assertEqual(exceptions.PARAMETER_FORMAT_ERROR, result['error_code'])

        # 运行云函数api
        data = {"slug": "show_api"}
        result = self.client.post('/api/show_api/', data=data).json()
        self.assertEqual('0', result['error_code'])
        result = result['result']
        self.assertEqual('show_api', result['slug'])
        self.assertEqual('api_db', result['app'])
        self.assertEqual('api', result['model'])
        self.assertEqual('func', result['operation'])
        self.assertEqual('show_api', result['func_name'])
