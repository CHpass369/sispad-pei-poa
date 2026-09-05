import os
from datetime import datetime
from celery.schedules import crontab
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env automaticamente para desarrollo local
dotenv_path = BASE_DIR.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-change-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.organizacion',
    'apps.gestion.apps.GestionConfig',
    'apps.catalogos',
    'apps.normativa',
    'apps.planificacion.apps.PlanificacionConfig',
    'apps.indicadores.apps.IndicadoresConfig',
    'apps.recursos.apps.RecursosConfig',
    'apps.techos.apps.TechosConfig',
    'apps.presupuesto.apps.PresupuestoConfig',
    'apps.territorio',
    'apps.pad.apps.PadConfig',
    'apps.workflow',
    'apps.documentos',
    'apps.reportes',
    'apps.auditoria',
    'apps.poau.apps.PoauConfig',
    'apps.modificaciones.apps.ModificacionesConfig',
    'apps.notificaciones',
    'apps.seguimiento.apps.SeguimientoConfig',
    'apps.priorizacion.apps.PriorizacionConfig',
    'apps.acciones_correctivas',
    'apps.articulacion.apps.ArticulacionConfig',
    'apps.codificacion.apps.CodificacionConfig',
    'apps.budget.apps.BudgetConfig',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'drf_spectacular',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.gis',
] + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.DeprecationV1Middleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get(
            'DB_ENGINE', 'django.contrib.gis.db.backends.postgis'
        ),
        'NAME': os.environ.get('DB_NAME', 'gams_pip'),
        'USER': os.environ.get('DB_USER', 'chpass369'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '/tmp/opencode'),
        'PORT': os.environ.get('DB_PORT', '5433'),
        # Cada peticion se envuelve en una transaccion: si la vista revienta a
        # mitad de camino, no queda media escritura confirmada. Django corre en
        # autocommit por omision, asi que sin esto la atomicidad es opcional y
        # depende de que alguien se acuerde de pedir transaction.atomic.
        # Para salirse a proposito existe @transaction.non_atomic_requests.
        'ATOMIC_REQUESTS': True,
        # PIP (ADR-003): search_path multi-esquema — public primero para que
        # migraciones futuras y PostGIS sigan funcionando; las tablas de dominio
        # viven en pip_core/pip_catalogo/sis_pe/sis_poa/sis_pro/pip_integracion/
        # pip_auditoria/pip_geo/reportes (migración física 2026-08-15).
        'OPTIONS': {
            'options': '-c search_path=public,pip_core,pip_catalogo,sis_pe,'
                       'sis_poa,sis_pro,pip_integracion,pip_auditoria,'
                       'pip_geo,reportes',
        },
        'TEST': {
            # Template con PostGIS preinstalado: evita requerir superusuario
            # para crear extensiones en la base de test.
            'TEMPLATE': os.environ.get('DB_TEST_TEMPLATE', 'template_postgis'),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# Prefijo de montaje. Vacío cuando la plataforma es dueña de su dominio; con
# valor cuando cuelga de una subruta de un nginx que ya atiende otro sistema
# en la misma dirección (el caso del servidor municipal: '/pip').
#
# nginx quita el prefijo antes de pasar la petición, así que las rutas de
# `urls.py` no cambian. Lo que sí cambia es la *generación*: sin
# FORCE_SCRIPT_NAME, `reverse()` devolvería '/admin/login/' y el navegador
# terminaría en el otro sistema.
URL_PREFIX = os.environ.get('DJANGO_URL_PREFIX', '').rstrip('/')

if URL_PREFIX:
    FORCE_SCRIPT_NAME = URL_PREFIX
    # No se activa USE_X_FORWARDED_HOST: nginx manda `Host $host` y nada más,
    # así que no hay nada que leer de X-Forwarded-Host. Encenderlo solo abriría
    # la puerta a que un cliente mande esa cabecera a mano y Django le crea.

STATIC_URL = f'{URL_PREFIX}/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Plantillas DOCX del expediente de preinversión (SISPRE / RM 115)
DOCUMENT_TEMPLATE_DIR = BASE_DIR / 'templates' / 'docx'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = f'{URL_PREFIX}/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Clave de cifrado de los documentos (32 bytes en base64). Vive fuera del
# repositorio y fuera de la base: si estuviera al lado del dato, cifrar no
# protegería de nada. Generar con:
#   python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"
DOCUMENTOS_CLAVE = os.environ.get('DOCUMENTOS_CLAVE', '')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.Usuario'

# Librerías GeoDjango (Windows local)
GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', '')
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH', '')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.api_exception_handler',
    # Rate limiting global deshabilitado. La plataforma se sirve detrás de nginx
    # con proxy_pass a 127.0.0.1 y sin NUM_PROXIES, así que DRF identifica a
    # todos los clientes con la misma IP: un único cubo horario dejaba fuera a
    # toda la institución a la vez. El throttle de login sigue activo.
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',
    },
}

# Deprecación API V1 (RFC 8594) — ver docs/refactor-pip/LEGACY_DEPRECATION.md
API_V1_SUNSET = 'Sun, 01 Jan 2027 00:00:00 GMT'
API_V1_DEPRECATION_LINK = '/docs/refactor-pip/LEGACY_DEPRECATION.md'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=4),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Vigencia del token de restablecimiento de contraseña (24 horas, coincide
# con el texto del email de reset; PasswordResetTokenGenerator).
PASSWORD_RESET_TIMEOUT = 86400

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:4200,http://127.0.0.1:4200'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# Orígenes desde los que Django acepta una petición que modifica datos.
# Es una lista aparte de CORS: CORS decide quién puede *leer* la respuesta,
# CSRF_TRUSTED_ORIGINS decide desde qué origen se acepta un POST. Sin el
# origen real acá, con DEBUG=False todo formulario responde 403 aunque la
# sesión sea válida — y el mensaje no menciona esta variable.
CSRF_TRUSTED_ORIGINS = [
    origen for origen in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:4200,http://127.0.0.1:4200',
    ).split(',') if origen.strip()
]

# Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'SISPOA Sacaba API',
    'DESCRIPTION': 'Sistema Integrado de Formulación, Seguimiento y Administración del POA',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Tareas programadas (celery beat) — WP-12
CELERY_BEAT_SCHEDULE = {
    'exportar-poa-completo-diario': {
        'task': 'apps.reportes.tasks.exportar_poa_completo_async',
        'schedule': crontab(hour=1, minute=0),
        'args': (datetime.now().year,),
    },
}

# Logging (WP-12): consola estructurada + archivo rotativo
(BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
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
            'filename': BASE_DIR / 'logs' / 'sispoa.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# File upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# =============================================================================
# Almacenamiento S3 (MinIO) — activar con USE_S3=True
# =============================================================================
from .settings_storage import *  # noqa

if USE_S3:  # noqa
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'}

# =============================================================================
# OIDC (Keycloak) — se activa cuando OIDC_RP_CLIENT_ID está presente
# Compatible con SimpleJWT: ambos mecanismos de autenticación coexisten.
# =============================================================================
from .settings_oidc import *  # noqa

# OIDC authentication backend (solo si OIDC está activo)
if USE_OIDC:  # noqa
    INSTALLED_APPS += ['mozilla_django_oidc']  # noqa

    AUTHENTICATION_BACKENDS = [
        'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    # SimpleJWT sigue siendo el método de autenticación API principal
    # OIDC para Django admin login via browser


# =============================================================================
# Endurecimiento de producción
# =============================================================================
# Cabeceras que no dependen del transporte: valen siempre que no sea desarrollo.
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'
    # nginx termina la conexión y reenvía por HTTP local: sin esta cabecera
    # Django cree que la petición llegó en claro y redirige en bucle.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Interruptor explícito, separado de DEBUG. Un despliegue puede ser de
# producción y todavía no tener certificado —el caso de una red interna
# que estrena servidor—, y en ese estado forzar HTTPS deja la plataforma
# inaccesible sin forma de entrar a diagnosticar.
#
# Mientras esté en False las sesiones viajan en claro: es un estado de
# transición, no un destino.
USE_HTTPS = os.environ.get('DJANGO_HTTPS', 'False').lower() in ('true', '1', 'yes')

if USE_HTTPS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS solo tiene sentido con un nombre de dominio: los navegadores lo
    # ignoran cuando el host es una dirección IP (RFC 6797, §8.1.1). Se activa
    # con DJANGO_HSTS=True el día que exista un nombre, no antes: encenderlo
    # contra un certificado que falla deja el sitio inalcanzable durante un
    # año y no se puede deshacer desde el servidor.
    if os.environ.get('DJANGO_HSTS', 'False').lower() in ('true', '1', 'yes'):
        SECURE_HSTS_SECONDS = 31536000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
