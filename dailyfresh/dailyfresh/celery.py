from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
# 设置默认的django配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')  

# 实例化Celery，参数为项目名称
app = Celery('dailyfresh')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# 加载所有注册应用下的tasks.py文件
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))