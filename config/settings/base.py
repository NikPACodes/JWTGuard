
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(",")
AUTH_USER_MODEL = "users.User"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TESTING = False

# --------------------------------------------------------------------------
# Application
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'apps.users.apps.UsersConfig',
    'apps.auth_jwt.apps.AuthJwtConfig',
    'apps.content.apps.ContentConfig',
]

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# --------------------------------------------------------------------------
# WSGI / ASGI / URLs
# --------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# --------------------------------------------------------------------------
# Template
# --------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
    },
}


# --------------------------------------------------------------------------
# Password validators
# --------------------------------------------------------------------------
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators
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


# --------------------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------------------
# https://docs.djangoproject.com/en/6.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static
# --------------------------------------------------------------------------
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = 'static/'
# STATICFILES_DIRS = [
#     BASE_DIR / 'static'
# ]
STATIC_ROOT = BASE_DIR / "staticfiles"


# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Единый формат ошибок для всего API.
    "EXCEPTION_HANDLER": "utils.exception_handler.custom_exception_handler",

    # Схема (по умолчанию)
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.auth_jwt.authentication.JWTAuthentication",
    ],

    # Запрет API без аутентификации (по умолчанию)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# --------------------------------------------------------------------------
# Spectacular
# --------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'DjangoJWT API',
    'DESCRIPTION': 'Advanced JWT authentication with Django + PyJWT + Redis-backed sessions',
    'VERSION': '1.0.0',

    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}


# --------------------------------------------------------------------------
# Redis
# --------------------------------------------------------------------------
REDIS_URL= os.getenv('REDIS_URL')

if REDIS_URL is None:
    REDIS_USERNAME = os.getenv('REDIS_USERNAME')
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')


# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------

JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'RS256')
JWT_ISSUER = os.getenv('JWT_ISSUER')
JWT_ACCESS_TTL_SECONDS = int(os.getenv('JWT_ACCESS_TTL_SECONDS', 900))
JWT_REFRESH_TTL_SECONDS = int(os.getenv('JWT_REFRESH_TTL_SECONDS', 604800))
JWT_PRIVATE_KEY_PATH = os.getenv('JWT_PRIVATE_KEY_PATH')
JWT_PUBLIC_KEY_PATH = os.getenv('JWT_PUBLIC_KEY_PATH')
JWT_REFRESH_REUSE_GRACE_SECONDS = int(os.getenv('JWT_REFRESH_REUSE_GRACE_SECONDS', 5))

