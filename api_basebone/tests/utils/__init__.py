import unittest

from django.db.models import Q

from parameterized import parameterized
from api_basebone.utils.operators import build_filter_conditions


class BuildFilterConditionsTest(unittest.TestCase):
    """测试构造过滤条件"""

    @parameterized.expand([
        (0, ),
        ('test', ),
        ([], ),
        ({}, ),
        ({'age': '23'}, ),
        ({'field': 'name', 'operator': ''}, ),
        ({'field': 'name', 'value': ''}, ),
        ({'value': 'name', 'operator': ''}, ),
    ])
    def test_with_invalid_data(self, data):
        """使用不合法的数据构造"""
        result = build_filter_conditions(data)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])

    def test_with_valid_data(self):
        """不使用排除的运算符"""
        data = [
            {'field': 'name', 'operator': '=', 'value': 23}
        ]
        result = build_filter_conditions(data)
        self.assertEqual(Q(name=23), result[0])
        self.assertIsNone(result[1])

    def test_with_exclude(self):
        """使用排除的运算符"""
        data = [
            {'field': 'name', 'operator': '!=', 'value': 23}
        ]
        result = build_filter_conditions(data)
        self.assertIsNone(result[0])
        self.assertEqual(Q(name=23), result[1])

    def test_with_all(self):
        """同时使用排除和非排除的运算符"""
        data = [
            {'field': 'name', 'operator': '!=', 'value': 23},
            {'field': 'age', 'operator': '=', 'value': 23},
        ]
        result = build_filter_conditions(data)
        self.assertEqual(Q(age=23), result[0])
        self.assertEqual(Q(name=23), result[1])
