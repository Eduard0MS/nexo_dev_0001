"""
Configuração WSGI para ambiente de produção.
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Defina a variável de ambiente para indicar ambiente de produção
os.environ.setdefault("DJANGO_ENVIRONMENT", "production")

# Defina o módulo de configurações Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")

from django.core.wsgi import get_wsgi_application

# Aplicação WSGI para produção
application = get_wsgi_application()
