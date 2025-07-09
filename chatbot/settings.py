"""
Django settings for chatbot project.
Generado con Django 5.0.4
"""

from pathlib import Path
import os
import dj_database_url          # pip install dj-database-url  (opcional pero práctico)

# ──────────────────────── Paths ────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────── Seguridad ────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")          # ### ← NUEVO
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"                   # ### ← NUEVO

ALLOWED_HOSTS = [
    "web-production-51ad.up.railway.app",   # tu subdominio Railway
    ".railway.app",                         # cualquier otro subdominio
    "localhost", "127.0.0.1",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")               # ### ← NUEVO
SESSION_COOKIE_SECURE = True                                                # ### ← NUEVO
CSRF_COOKIE_SECURE    = True                                                # ### ← NUEVO
CSRF_TRUSTED_ORIGINS  = ["https://*.railway.app"]                           # ### ← NUEVO

SECURE_CROSS_ORIGIN_OPENER_POLICY = None   # mantiene tu ajuste


# ──────────────────────── Apps ────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "chatbot_app",
]

# ──────────────────────── Middleware ────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chatbot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
WSGI_APPLICATION = "chatbot.wsgi.application"
ASGI_APPLICATION  = "chatbot.asgi.application"

# ──────────────────────── Channel layer (Redis) ────────────────────────
CHANNEL_LAYERS = {                                           # ### ← CAMBIADO
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")],
        },
    },
}

# ──────────────────────── Base de datos ────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")                # Railway inyecta esto si usas Postgres
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ──────────────────────── Contraseñas ────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ──────────────────────── Localización ────────────────────────
LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"          # ### ← usa tu zona
USE_I18N  = True
USE_TZ    = True                         # conserva timestamps en UTC internamente

# ──────────────────────── Archivos estáticos ────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # collectstatic los pondrá aquí en Railway

# ──────────────────────── Clave primaria por defecto ────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
