"""Settings de prueba sin Docker: SQLite + apps mínimas.

Permite correr tests de las apps que NO usan campos geo (PostGIS)
directamente con el venv local, sin base de datos Docker:

    cd backend
    .venv\\Scripts\\python.exe -m pytest apps/accounts/tests.py \
        -q --ds=config.settings_test_sqlite

NO usar para la suite completa: las apps con modelos geo
(territorio, inversion) requieren PostgreSQL/PostGIS.
"""
from .settings import *  # noqa: F403

# --- Base de datos: SQLite en memoria (solo para tests) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# --- Aplicaciones: todas las locales NO-geo (territorio/inversion requieren
# --- PostgreSQL/PostGIS y quedan fuera de este settings).
LOCAL_APPS_TEST = [
    'apps.core',
    'apps.accounts',
    'apps.organizacion',
    'apps.gestion',
    'apps.catalogos',
    'apps.normativa',
    'apps.planificacion',
    'apps.indicadores',
    'apps.recursos',
    'apps.techos',
    'apps.presupuesto',
    'apps.pad',
    'apps.workflow',
    'apps.documentos',
    'apps.reportes',
    'apps.auditoria',
    'apps.poau',
    'apps.evaluacion',
    'apps.modificaciones',
    'apps.notificaciones',
    'apps.seguimiento',
    'apps.acciones_correctivas',
    'apps.articulacion',
    'apps.codificacion',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    *LOCAL_APPS_TEST,
]

# --- Sin migraciones: el esquema se crea directo desde los modelos.
# --- SQLite no puede ejecutar los triggers plpgsql de las migraciones
# --- (articulacion/catalogos/codificacion/presupuesto) y el grafo de
# --- migraciones cruza apps, así que no se ejecuta ninguna. Los seeds que
# --- los tests presuponen los siembra tests/conftest.py (reutilizando las
# --- funciones seed de las data migrations) cuando SETTINGS_MODULE es este.
MIGRATION_MODULES = {
    label: None
    for label in [
        'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
        'core', 'accounts', 'organizacion', 'gestion', 'catalogos',
        'normativa', 'planificacion', 'indicadores', 'recursos', 'techos',
        'presupuesto', 'pad', 'workflow', 'documentos', 'reportes',
        'auditoria', 'poau', 'evaluacion', 'modificaciones',
        'notificaciones', 'seguimiento', 'acciones_correctivas',
        'articulacion', 'codificacion',
    ]
}

# --- Middleware mínimo para DRF/SimpleJWT en tests ---
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls_test_sqlite'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
        ],
    },
}]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email en memoria para tests (django.core.mail.outbox)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Sin throttling en tests
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None,
        'login': None,
    },
}
