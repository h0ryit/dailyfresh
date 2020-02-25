'''使用celery'''

from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.conf import settings
from django.shortcuts import reverse
from django.core.mail import send_mail


@shared_task
def send_register_active_email(to_email, username, token):
    ''' 发送激活邮件'''
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    url = "http://" + settings.IP_PORT + reverse('user:active', kwargs={'token':token})
    html_message = ''' <h1>%s, 欢迎您成为天天生鲜注册会员</h1><br/>请点击以下链接激活您的账户<br/><a href="%s">%s</a>''' % (username, url, url)
    send_mail(subject, message, sender, receiver, html_message=html_message)