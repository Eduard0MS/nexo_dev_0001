from pathlib import Path
import os
import io
import sys

from dotenv import load_dotenv, find_dotenv

# ╭────────────────── utilitário .env ──────────────────╮
_ENV_LOADED = False
def log_once(message: str):
    cache = getattr(sys.modules[__name__], "_PRINTED_MESSAGES", set())
    if message not in cache:
        print(message)
        cache.add(message)
        sys.modules[__name__]._PRINTED_MESSAGES = cache

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_safely():
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    try:
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)
            log_once(f"Arquivo .env encontrado em: {env_file}")
            _ENV_LOADED = True
            return
    except Exception as exc:
        log_once(f"Erro ao carregar .env normalmente: {exc}")

    alt = BASE_DIR / ".env"
    if alt.exists():
        with alt.open("r", encoding="utf-8-sig") as fh:
            load_dotenv(stream=io.StringIO(fh.read()))
            log_once("Arquivo .env carregado com utf-8-sig")
            _ENV_LOADED = True
            return

    log_once("Arquivo .env não encontrado ou não pôde ser carregado!")

load_env_safely()
# ╰───────────────────────────────────────────────────────╯

# ─────── Ambiente ───────
ENVIRONMENT   = os.getenv("DJANGO_ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
log_once(f"DEBUG: Ambiente atual = {ENVIRONMENT}")
log_once(f"DEBUG: IS_PRODUCTION = {IS_PRODUCTION}")

# ─────── Segurança básica ───────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-...")
DEBUG      = not IS_PRODUCTION
ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if IS_PRODUCTION
    else ["localhost", "127.0.0.1", "10.209.15.176"]
)

# ─────── Apps ───────
INSTALLED_APPS = [
    # Contribs
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    # Yours
    "core",
    # Extras
    "rest_framework",
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]

CRISPY_TEMPLATE_PACK = "bootstrap4"
SITE_ID = 1

# ─────── URLs de auth ───────
LOGIN_URL          = "/login_direct/"
LOGIN_REDIRECT_URL = "/home/"
LOGOUT_REDIRECT_URL = "/login_direct/"

# ─────── Segurança HTTPS (produção) ───────
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT          = True
    SECURE_PROXY_SSL_HEADER      = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE        = True
    CSRF_COOKIE_SECURE           = True
    SECURE_HSTS_SECONDS          = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD          = True
    SECURE_CONTENT_TYPE_NOSNIFF  = True
    SECURE_BROWSER_XSS_FILTER    = True
    X_FRAME_OPTIONS              = "DENY"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY    = True

# ─────── Middleware & URLs ───────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "Nexus.urls"

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

WSGI_APPLICATION = "Nexus.wsgi.application"

# ─────── Bancos ───────
if IS_PRODUCTION:
    log_once("DEBUG: Usando configurações de PRODUÇÃO")
    DATABASES = {
        "default": {
            "ENGINE":   os.getenv("DB_ENGINE",   "django.db.backends.postgresql"),
            "NAME":     os.getenv("DB_NAME",     "nexus_prod"),
            "USER":     os.getenv("DB_USER",     ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST":     os.getenv("DB_HOST",     "localhost"),
            "PORT":     os.getenv("DB_PORT",     "5432"),
        }
    }
else:
    log_once("DEBUG: Usando configurações de DESENVOLVIMENTO")
    DATABASES = {
        "default": {
            "ENGINE":   "django.db.backends.mysql",
            "NAME":     "nexo_dev",
            "USER":     "root",
            "PASSWORD": "1802Edu0#*#",
            "HOST":     "127.0.0.1",
            "PORT":     "3306",
        }
    }

# ─────── Auth backends & validações ───────
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ["username", "email"], "max_similarity": 0.7},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────── Localização ───────
LANGUAGE_CODE = "pt-br"
TIME_ZONE     = "America/Sao_Paulo"
USE_I18N      = True
USE_TZ        = True

# Configurações de arquivos estáticos
STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações do allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
# ╭────────── Estáticos & mídia ──────────╮
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = "/var/www/nexo_static"

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# ╰───────────────────────────────────────╯

# ─────── allauth ───────
ACCOUNT_EMAIL_REQUIRED            = True
ACCOUNT_USERNAME_REQUIRED         = False
ACCOUNT_AUTHENTICATION_METHOD     = "email"
ACCOUNT_EMAIL_VERIFICATION        = "mandatory"
ACCOUNT_UNIQUE_EMAIL              = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

SOCIALACCOUNT_EMAIL_REQUIRED    = True
SOCIALACCOUNT_AUTO_SIGNUP       = True
SOCIALACCOUNT_LOGIN_ON_GET      = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL       = True
SOCIALACCOUNT_PROVIDERS         = {}

ACCOUNT_ADAPTER       = "allauth.account.adapter.DefaultAccountAdapter"
SOCIALACCOUNT_ADAPTER = "core.adapters.CustomSocialAccountAdapter"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────── Logging (produção) ───────
if IS_PRODUCTION:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "file": {
                "level":    "ERROR",
                "class":    "logging.FileHandler",
                "filename": BASE_DIR / "logs/django-errors.log",
                "formatter":"verbose",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level":    "ERROR",
                "propagate": True,
            },
        },
    }
