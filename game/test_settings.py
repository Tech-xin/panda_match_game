"""
测试配置文件，用于设置测试环境

这个文件不是测试文件，而是一个配置文件，用于在运行测试时覆盖默认设置。
要使用这个配置文件，需要在运行测试时指定：
DJANGO_SETTINGS_MODULE=game.test_settings
"""

# 导入项目设置作为基础
from panda_match.settings import *

# 使用内存数据库进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 禁用缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# 使用测试密码哈希器，加快测试速度
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 禁用CSRF保护，简化测试
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if middleware != 'django.middleware.csrf.CsrfViewMiddleware'
]

# 设置媒体根目录为临时目录
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

# 设置静态文件目录
STATIC_ROOT = tempfile.mkdtemp()

# 设置日志级别
import logging
logging.disable(logging.CRITICAL)

# 设置测试运行器
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# 设置测试模式
DEBUG = False
TEMPLATE_DEBUG = False

# 设置邮件后端
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend' 