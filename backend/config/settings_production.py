"""
Settings de producción para SISPOA Sacaba.
Sobreescribe config/settings.py con valores seguros para despliegue.

Uso:
    DJANGO_SETTINGS_MODULE=config.settings_production python manage.py runserver
    # o en producción con Gunicorn:
    DJANGO_SETTINGS_MODULE=config.settings_production gunicorn config.wsgi
"""
import os
from .settings import *  # noqa: F403

# === SEGURIDAD ===
DEBUG = False

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Obligatorio en producción

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'sispoa.gamsacaba.gob.bo,localhost'
).split(',')

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Database (desde variables de entorno)
DATABASES['default'].update({  # noqa: F405
    'ENGINE': os.environ.get('DB_ENGINE', 'django.contrib.gis.db.backends.postgis'),
    'NAME': os.environ['DB_NAME'],
    'USER': os.environ['DB_USER'],
    'PASSWORD': os.environ['DB_PASSWORD'],
    'HOST': os.environ.get('DB_HOST', 'localhost'),
    'PORT': os.environ.get('DB_PORT', '5432'),
    'CONN_MAX_AGE': 60,
    'OPTIONS': {
        'connect_timeout': 10,
    },
})

# CORS en producción
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://sispoa.gamsacaba.gob.bo'
).split(',')

# JWT más restrictivo
SIMPLE_JWT.update({  # noqa: F405
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # noqa: F405
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # noqa: F405
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
})

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/sispoa/django.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}

# Archivos estáticos y media
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/sispoa/static')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/var/www/sispoa/media')

# Rate limiting
REST_FRAMEWORK.update({  # noqa: F405
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
})
