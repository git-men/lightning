from celery import shared_task

from api_basebone.core.exceptions import BusinessException
from api_basebone.utils.dingding import dingding_robot
from bsm_config.settings import site_setting
from django.core.mail import get_connection, send_mail, EmailMessage
from django.core.mail.message import EmailMessage


@shared_task
def dingding_robot_push(data, access_token_type='default'):
    """钉钉机器人发送消息"""
    dingding_robot.push_message(data, access_token_type=access_token_type)

@shared_task
def send_email(subject, body, mail_to):
    if not site_setting['mail_protocol']:
        raise BusinessException(error_message='未配置邮件配置')
    with get_connection(
        host=site_setting['mail_host'],
        port=site_setting['mail_port'],
        username=site_setting['mail_need_login'] and site_setting['mail_username'],
        password=site_setting['mail_need_login'] and site_setting['mail_password'],
        use_tls=site_setting['start_tls'],
        use_ssl=site_setting['mail_protocol'] == 'SMTP_SSL',
    ) as connection:
        if type(mail_to) not in [tuple, list]:
            mail_to = [mail_to]
        print(send_mail(subject, body, f"{site_setting['sender_name']} <{site_setting['sender_address']}>",  mail_to, connection=connection))
