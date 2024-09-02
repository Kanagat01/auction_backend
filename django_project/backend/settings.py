import os
from pathlib import Path

from django.utils import timezone

BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_USER_MODEL = 'api_users.UserModel'
USERNAME_FIELD = 'email'

SECRET_KEY = os.environ.get(
    "SECRET_KEY", default="django-insecure-3b!7h8__f5e2frki-d&*)gb5y@--&*e&#oh=41y)cq%jwh$g5c")

DEBUG = bool(os.environ.get("DEBUG", default=1))

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost 127.0.0.1 10.0.2.2").split(" ")
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost http://127.0.0.1").split(" ")

CORS_ALLOW_ALL_ORIGINS = True

REACT_RESET_PASSWORD_URL = os.environ.get(
    "REACT_RESET_PASSWORD_URL", "http://localhost:5173/reset-password-confirm/")

SMS_LOGIN = os.environ.get(
    "SMS_LOGIN", "")
SMS_PASSWORD = os.environ.get(
    "SMS_PASSWORD", "")


if "cargonika.ru" not in ALLOWED_HOSTS:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_HOST_USER = "example@gmail.com"
else:
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))
    EMAIL_USE_SSL = bool(os.environ.get("EMAIL_USE_SSL"))


INSTALLED_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_q',
    'api_users',
    'api_payments',
    'api_notification',
    'api_auction',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = "backend.asgi.application"

#
AUTH_TOKEN_VALIDITY = timezone.timedelta(days=1)
REST_FRAMEWORK = {
    'NON_FIELD_ERRORS_KEY': 'errors',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'api_users.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'backend.global_functions.custom_exception_handler',
}

# Database

if os.environ.get('RUNNING_FROM_DOCKER', False):
    print("USING POSTGRESQL DATABASE")
    DATABASES = {
        "default": {
            "ENGINE": 'django.db.backends.postgresql',
            "NAME": os.environ.get("POSTGRES_DB"),
            "USER": os.environ.get("POSTGRES_USER"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("POSTGRES_HOST"),
            "PORT": os.environ.get("POSTGRES_PORT"),
        }
    }

else:
    print("USING SQLITE DATABASE")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# Logging
LOGGING = {}

if os.environ.get('RUNNING_FROM_DOCKER', False):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO' if DEBUG else 'ERROR',
                'class': 'logging.FileHandler',
                'filename': './logs.log',
                'formatter': 'verbose'
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'INFO' if DEBUG else 'ERROR',
                'propagate': True,
            },
        },
    }

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

Q_CLUSTER = {
    'name': 'backend',
    'workers': 3,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q2',
    'orm': 'default',
    'ack_failures': True,
    'max_attempts': 1,
    'attempt_count': 1
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get('REDIS_HOST', "127.0.0.1"), os.environ.get('REDIS_PORT', '6379'))],
        },
    },
}
