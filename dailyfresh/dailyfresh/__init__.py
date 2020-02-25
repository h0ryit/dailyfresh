from __future__ import absolute_import, unicode_literals

import pymysql

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app


pymysql.version_info = (1, 3, 13, "final", 0)
pymysql.install_as_MySQLdb()


__all__ = ('celery_app',)
