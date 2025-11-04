import os 
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='unsafe-secret')

# SECURITY WARNING: don't run with debug turned on in production!
# --- DEV OPEN MODE: libera CORS e CSRF para dev ---
DEBUG = config('DEBUG', cast=bool, default=True)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='*')

# Se você está atrás de proxy/ingress terminando HTTPS (Nginx/Traefik)
USE_X_FORWARDED_PROTO = config('USE_X_FORWARDED_PROTO', cast=bool, default=True)
if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF
# Em DEV, preenche automaticamente os origins mais comuns
if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'https://api.alvelos.com',
        'http://api.alvelos.com',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
else:
    # Em produção, use apenas os domínios oficiais
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv(), default='')

# Cookies (dev friendly)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "drf_spectacular",
    "drf_spectacular_sidecar", 
    'rest_framework',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',
    'authentication',
    'auditlog',
    # 'banking',
]

MIDDLEWARE = [
    "auditlog.middleware.RequestIDMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "auditlog.middleware.AuditMiddleware",
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

###############################################################################

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=25)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=False)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default=False)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default=None)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@localhost")
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", cast=int, default=30)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": "10/min",
        "auth_recovery": "5/min",
        "auth_otp": "12/min",
        "auth_register": "5/min",
        "anon": "100/min",
    },
    # Opcional: paginação, etc.
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
REST_FRAMEWORK.update({
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
})

SPECTACULAR_SETTINGS = {
    "TITLE": "Veloma ERP/CRM API",
    "DESCRIPTION": "API para escritório de contabilidade (PT). Autenticação por JWT. Perfis: admin, staff, client.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # vamos expor manualmente as rotas /schema/
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "CONTACT": {"name": "Suporte", "email": "suporte@velomacontabilidade.com"},
    # Segurança (JWT no header Authorization: Bearer <token>)
    "SECURITY": [{"bearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    # tags sugeridas
    "TAGS": [
        {"name": "Auth", "description": "Registro, login, OTP, reset, verificação de e-mail"},
        {"name": "Users", "description": "Gestão de utilizadores (staff/admin)"},
        {"name": "Clients", "description": "Gestão de clientes e auto-serviço (client)"},
        {"name": "Documents", "description": "Uploads, faturação, SAFT"},
        {"name": "Reports", "description": "Relatórios, períodos de IVA, prazos"},
        {"name": "Integrations", "description": "Integrações externas, storage"},
        {"name": "Audit", "description": "Eventos e rastreabilidade"},
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# ---- Redis (cache opcional) ----
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config('REDIS_URL', default='redis://127.0.0.1:6379/0'),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# ---- Celery ----
CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Escolha do backend
STORAGE_BACKEND = config("STORAGE_BACKEND", default="minio")  # "minio" ou "local"

# MinIO
MINIO_ENDPOINT = config("MINIO_ENDPOINT", default="127.0.0.1:9002")  # tua porta mapeada
MINIO_ACCESS_KEY = config("MINIO_ACCESS_KEY", default="")
MINIO_SECRET_KEY = config("MINIO_SECRET_KEY", default="")
MINIO_BUCKET = config("MINIO_BUCKET", default="veloma")
MINIO_SECURE = config("MINIO_SECURE", cast=bool, default=False)
MINIO_REGION = config("MINIO_REGION", default=None)
MINIO_PREFIX = config("MINIO_PREFIX", default="")  # opcional, ex: "prod"

# Storage local (dev)
LOCAL_STORAGE_DIR = config("LOCAL_STORAGE_DIR", default=None)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.core.mail": {"handlers": ["console"], "level": "DEBUG"},
    },
}