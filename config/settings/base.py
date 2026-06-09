from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.siggo_readonly",
    "apps.users",
    "apps.organizacion",
    "apps.catalogo",
    "apps.inventario",
    "apps.almacen",
    "apps.tickets",
    "apps.documentos",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ──────────────────────────────────────────────
# Bases de datos
# ──────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("SIGTIC_DB_NAME", default="sigtic_db"),
        "USER": env("SIGTIC_DB_USER", default="sigtic"),
        "PASSWORD": env("SIGTIC_DB_PASSWORD", default=""),
        "HOST": env("SIGTIC_DB_HOST", default="localhost"),
        "PORT": env("SIGTIC_DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    },
    # bdsiggo — solo lectura, PostgreSQL ~8.x legado
    # Conexión activada solo si SIGGO_DB_HOST está configurado
    "siggo": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("SIGGO_DB_NAME", default="bdsiggo"),
        "USER": env("SIGGO_DB_USER", default=""),
        "PASSWORD": env("SIGGO_DB_PASSWORD", default=""),
        "HOST": env("SIGGO_DB_HOST", default=""),
        "PORT": env("SIGGO_DB_PORT", default="5432"),
        # No usamos default_transaction_read_only (no soportado en PG 8)
        # El router se encarga de bloquear escrituras a nivel Django
        "TEST": {"NAME": None},
        "CONN_MAX_AGE": 30,
    },
}

DATABASE_ROUTERS = ["routers.db_router.SiggoRouter"]

# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "apps.users.backends.SiggoAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ──────────────────────────────────────────────
# DRF
# ──────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.cookie_auth.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.FlexPageNumberPagination",
    "PAGE_SIZE": 25,
}

# ──────────────────────────────────────────────
# JWT — tokens en httpOnly cookies
# ──────────────────────────────────────────────
_ACCESS_MINUTES = env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60)
_REFRESH_DAYS = env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=_ACCESS_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=_REFRESH_DAYS),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Configuración de las cookies JWT
JWT_COOKIE_NAME = "sigtic_access"
JWT_REFRESH_COOKIE_NAME = "sigtic_refresh"
JWT_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=False)
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = env("JWT_COOKIE_SAMESITE", default="Lax")
JWT_COOKIE_PATH = "/"

# ──────────────────────────────────────────────
# drf-spectacular
# ──────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "SIGTIC API",
    "DESCRIPTION": (
        "## Sistema de Gestión de Tickets TI — Unidad de Informática Municipal\n\n"
        "### Autenticación\n"
        "Esta API usa **JWT en httpOnly cookies** (no headers). "
        "Llama primero a `POST /api/v1/auth/login/` con `{username, password}`. "
        "El servidor responde seteando las cookies `sigtic_access` y `sigtic_refresh` automáticamente.\n\n"
        "Desde Swagger UI activa **'Include credentials'** (candado) para que las cookies se envíen.\n\n"
        "### Flujo de estados de ticket\n"
        "`ENVIADO > EN_REVISION > ASIGNADO > EN_ATENCION > SOLUCIONADO | EN_MANTENIMIENTO | TERCERIZADO > FINALIZADO`\n\n"
        "Desde cualquier estado no terminal: `> RECHAZADO` (solo JEFE_INFO / ENCARGADO_INFO activo)."
    ),
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "ENUM_NAME_OVERRIDES": {
        "EstadoTicketEnum":       "apps.tickets.models.EstadoTicket",
        "EstadoDispositivoEnum":  "apps.inventario.models.EstadoDispositivo",
        "RolSigticEnum":          "apps.users.models.RolSigtic",
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.spectacular_hooks.assign_tags_by_path",
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 2,
        "docExpansion": "list",
        "filter": True,
        "tryItOutEnabled": True,
    },
}

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:4200"],
)
CORS_ALLOW_CREDENTIALS = True  # necesario para enviar cookies cross-origin

# ──────────────────────────────────────────────
# Internacionalización
# ──────────────────────────────────────────────
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# Static / Media
# ──────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────
# Siggo settings
# ──────────────────────────────────────────────
# Algoritmo usado para verificar passwords de bdsiggo: md5 | sha1 | bcrypt
SIGGO_PASSWORD_ALGO = env("SIGGO_PASSWORD_ALGO", default="md5")
