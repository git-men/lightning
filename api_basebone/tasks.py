from celery import shared_task
from api_basebone.utils.dingding import dingding_robot


@shared_task
def dingding_robot_push(data, access_token_type='default'):
    """钉钉机器人发送消息"""
    dingding_robot.push_message(data, access_token_type=access_token_type)
