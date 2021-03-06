"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ofmoam8w62whr66*7_a9*v@&t!#2)^5!7&9%qoof=ff+95#uxs'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cart.apps.CartConfig',
    'user.apps.UserConfig',
    'goods.apps.GoodsConfig',
    'order.apps.OrderConfig',
    'tinymce',      # 富文本编辑器
    'haystack',     # 全文检索框架

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',     # 配置media
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': [
                'django.templatetags.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'USER': 'whoie',
        'PASSWORD': 'whoie',
        'HOST': '192.168.117.175',
        'PORT': 3306,
    }
}


#富文本
TINYMCE_DEFAULT_CONFIG = {
    'theme':'advanced',
    'width': 600,
    'height': 400,
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

AUTH_USER_MODEL = 'user.User'

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

# 发送邮件配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'h0ryit@163.com'      # 发送邮件的邮箱
EMAIL_HOST_PASSWORD = 'h0ryit'      # 在邮箱中设置的客户端授权密码
EMAIL_FROM = '天天生鲜<h0ryit@163.com>'     # 收件人看到的发件人


# 监听的IP和端口
IP_PORT = "192.168.117.172:8000"


# Celery Config

CELERY_TIMEZONE = 'Asia/Shanghai'
# 中间人配置信息
CELERY_BROKER_URL = 'redis://192.168.117.175:6379/1'
CELERY_RESULT_BACKEND = 'redis://192.168.117.175:6379/1'

# 设置不自动关联is_active
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']


# django缓存配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.117.175:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


# session配置
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# 默认登录页面
LOGIN_URL = "/user/login"

# 静态文件目录
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# 收集静态文件的路径
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 动态文件目录
MEDIA_URL = '/media/'
MEDIA_DIR = os.path.join(BASE_DIR, "media")
# 收集动态文件的路径
MEDIA_ROOT = MEDIA_DIR

# 全文检索框架haystack配置
HAYSTACK_CONNECTIONS = {
    'default': {
        #使用whoosh引擎
        'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        #索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}

#当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

ALIPAY = {
    'appid':"2016101900723111",  # appid
    'app_notify_url':None,      # 默认回调url
    'app_private_key_string':os.path.join(BASE_DIR, 'apps/order/app_private_key.pem'),     # 应用私钥
    'alipay_public_key_string':os.path.join(BASE_DIR, 'apps/order/alipay_public_key.pem'), # 支付宝的公钥
    'sign_type':"RSA2",  # RSA 或者 RSA2
    'debug':True  # 默认False
}
