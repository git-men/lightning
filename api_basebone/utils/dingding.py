import json
import requests

from django.conf import settings


class DingDingRobot:
    """钉钉消息通知机器人"""

    BASE_URL = 'https://oapi.dingtalk.com/robot/send?access_token={}'

    def _get_url(self, access_token):
        return self.BASE_URL.format(access_token)

    def _push_notify(self, data, access_token_type='default'):
        """推送通知, 通知只会通知文本消息

        Params:
            access_token str 消息机器人的访问令牌
            data str | dict | tuple 数据
        """
        access_token_map = getattr(settings, 'DINGDING_ROBOT_ACCESS_TOKEN_MAP', None)
        if not access_token_map or not isinstance(access_token_map, dict):
            return

        if access_token_type not in access_token_map:
            return

        access_token = access_token_map[access_token_type]
        if not access_token:
            return

        if not isinstance(data, str):
            try:
                data = str(data)
            except Exception:
                return

        content = {
            "msgtype": "text",
            "text": {
                "content": data
            }
        }

        url = self._get_url(access_token)

        try:
            requests.post(url, json=content)
        except Exception:
            pass

    def push_message(self, data, access_token_type='default'):
        """推送消息"""
        self._push_notify(data, access_token_type=access_token_type)


dingding_robot = DingDingRobot()
