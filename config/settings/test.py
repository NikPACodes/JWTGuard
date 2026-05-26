"""
Test - настройки для тестов
"""
from dotenv import load_dotenv
from pathlib import Path

ENV_TEST_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ENV_TEST_DIR / '.env.test')

from .base import *

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = False
TESTING = True


# --------------------------------------------------------------------------
# Password
# --------------------------------------------------------------------------
# Добавили для ускорения тестов
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# # --------------------------------------------------------------------------
# # Django REST Framework
# # --------------------------------------------------------------------------
# REST_FRAMEWORK = {
#     **REST_FRAMEWORK,
#     'DEFAULT_RENDERER_CLASSES': [
#         # Рендер для превращения объектов в JSON
#         'rest_framework.renderers.JSONRenderer',
#     ]
# }

# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------
JWT_ACCESS_TTL_SECONDS = int(os.getenv('JWT_ACCESS_TTL_SECONDS', 60))
JWT_REFRESH_TTL_SECONDS = int(os.getenv('JWT_REFRESH_TTL_SECONDS', 120))
JWT_REFRESH_REUSE_GRACE_SECONDS = int(os.getenv('JWT_REFRESH_REUSE_GRACE_SECONDS', 0))
