from pathlib import Path
import os
from dotenv import load_dotenv, find_dotenv
import io
import sys

# Variável para controlar se as mensagens já foram exibidas
_ENV_LOADED = False

# Função para exibir mensagens de log apenas uma vez
def log_once(message):
    """Imprime uma mensagem apenas uma vez por processo Python."""
    global _PRINTED_MESSAGES
    if not hasattr(sys.modules[__name__], '_PRINTED_MESSAGES'):
        sys.modules[__name__]._PRINTED_MESSAGES = set()
    
    if message not in sys.modules[__name__]._PRINTED_MESSAGES:
        print(message)
        sys.modules[__name__]._PRINTED_MESSAGES.add(message)

# Definir diretório base
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis de ambiente do arquivo .env com tratamento robusto de erros
def load_env_safely():
    global _ENV_LOADED
    
    # Se já carregamos o .env, não precisamos fazer de novo
    if _ENV_LOADED:
        return
        
    try:
        # Tentativa padrão de encontrar e carregar o .env
        ENV_FILE = find_dotenv()
        if ENV_FILE:
            load_dotenv(ENV_FILE)
            log_once(f"Arquivo .env encontrado em: {ENV_FILE}")
            _ENV_LOADED = True
            return
    except Exception as e:
        log_once(f"Erro ao carregar .env normalmente: {e}")
    
    # Alternativa 1: Tentar carregar com codificação explícita
    try:
        env_path = os.path.join(BASE_DIR, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig lida com BOM
                content = f.read()
                # Criar um arquivo em memória que python-dotenv possa ler
                stream = io.StringIO(content)
                load_dotenv(stream=stream)
                log_once("Arquivo .env carregado com encoding utf-8-sig")
                _ENV_LOADED = True
                return
    except Exception as e:
        log_once(f"Erro ao carregar .env com utf-8-sig: {e}")
    
    # Se tudo falhar, informamos que o .env não foi encontrado
    log_once("Arquivo .env não encontrado ou não pôde ser carregado!")

# Chamar nossa função segura
load_env_safely()

# Apenas indicar que variáveis de banco foram carregadas
log_once("DEBUG: Variáveis de banco carregadas")

# Definir ambiente
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'
log_once(f"DEBUG: Ambiente atual = {ENVIRONMENT}")
log_once(f"DEBUG: IS_PRODUCTION = {IS_PRODUCTION}")

# CONFIGURAÇÕES DE SEGURANÇA
# Em produção, use variáveis de ambiente para SECRET_KEY
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', "django-insecure-...")

# DEBUG é False em produção
DEBUG = not IS_PRODUCTION

# ALLOWED_HOSTS configurado apenas em produção
if IS_PRODUCTION:
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "apps.core",
    "rest_framework",
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]
CRISPY_TEMPLATE_PACK = "bootstrap4"
SITE_ID = 1
STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# URLs de autenticação
LOGIN_URL = "/login_direct/"  # nome da rota 'login'
LOGIN_REDIRECT_URL = "/home/"  # nome da rota 'home'
LOGOUT_REDIRECT_URL = "/login_direct/"  # nome da rota 'logout'

# Configurações de Segurança HTTPS (ativas apenas em produção)
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# Configurações de Cookies (sempre ativas)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Ajuste conforme sua estrutura
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

# Configurações de banco de dados
if IS_PRODUCTION:
    log_once("DEBUG: Usando configurações de PRODUÇÃO")
    DATABASES = {
        "default": {
            "ENGINE": os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
            "NAME": os.environ.get('DB_NAME', 'nexus_prod'),
            "USER": os.environ.get('DB_USER', ''),
            "PASSWORD": os.environ.get('DB_PASSWORD', ''),
            "HOST": os.environ.get('DB_HOST', 'localhost'),
            "PORT": os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    log_once("DEBUG: Usando configurações de DESENVOLVIMENTO")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "nexo_dev"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "1802Edu0#*#"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
        }
    }

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ["username", "email"],
            "max_similarity": 0.7,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

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
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Social Account Settings
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = False
SOCIALACCOUNT_QUERY_EMAIL = True

# Social Account Configuration - Remover provedores sociais
SOCIALACCOUNT_PROVIDERS = {}

# Configurações para resolver o loop de redirecionamento
LOGIN_REDIRECT_URL = "/home/"
ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"
SOCIALACCOUNT_ADAPTER = (
    "core.adapters.CustomSocialAccountAdapter"  # Usando nosso adaptador personalizado
)

# Permitir criar contas sem e-mail verificado
SOCIALACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

# Desativar formulários de signup sociais
SOCIALACCOUNT_FORMS = {}

# Desativar o processo de signup social para evitar o redirecionamento
SOCIALACCOUNT_AUTO_SIGNUP = True

# Configurações de logging para produção
if IS_PRODUCTION:
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
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': os.path.join(BASE_DIR, 'logs/django-errors.log'),
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
