#!/usr/bin/env python
"""
Script para verificar se o ambiente de produção está configurado corretamente.
Execute este script antes de implantar em produção.
"""

import os
import sys
import django
from dotenv import load_dotenv

# Verificar se o arquivo .env existe
if not os.path.exists('.env'):
    print("ERRO: Arquivo .env não encontrado!")
    print("Por favor, crie um arquivo .env com as configurações de produção.")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
os.environ.setdefault('DJANGO_ENVIRONMENT', 'production')
django.setup()

from django.conf import settings

# Lista de verificações
checks = [
    ('DEBUG está desativado', not settings.DEBUG),
    ('ALLOWED_HOSTS está configurado', len(settings.ALLOWED_HOSTS) > 0 and settings.ALLOWED_HOSTS != ['*']),
    ('SECRET_KEY foi alterada', settings.SECRET_KEY != 'django-insecure-...'),
    ('HTTPS está configurado', settings.SECURE_SSL_REDIRECT),
    ('HSTS está configurado', settings.SECURE_HSTS_SECONDS > 0),
    ('Cookies seguros estão configurados', settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE),
    ('Cookies HTTP-only estão configurados', settings.SESSION_COOKIE_HTTPONLY and settings.CSRF_COOKIE_HTTPONLY),
    ('Diretório de logs existe', os.path.isdir('logs')),
]

print("\n== VERIFICAÇÃO DE AMBIENTE DE PRODUÇÃO ==\n")

all_passed = True
for description, passed in checks:
    status = "✓ PASSOU" if passed else "✗ FALHOU"
    color = "\033[92m" if passed else "\033[91m"  # Verde ou vermelho
    print(f"{color}{status}\033[0m - {description}")
    if not passed:
        all_passed = False

print("\n== CONFIGURAÇÕES DE BANCO DE DADOS ==\n")
db_config = settings.DATABASES['default']
if db_config['ENGINE'] == 'django.db.backends.sqlite3':
    print("\033[91m✗ AVISO: Usando SQLite em produção!\033[0m")
    print("Recomendamos usar PostgreSQL, MySQL ou outro banco de dados adequado para produção.")
    all_passed = False
else:
    print(f"\033[92m✓ OK\033[0m - Usando {db_config['ENGINE']}")

print("\n== VARIÁVEIS DE AMBIENTE CRÍTICAS ==\n")
env_vars = [
    'DJANGO_SECRET_KEY',
    'DJANGO_ALLOWED_HOSTS',
    'DJANGO_ENVIRONMENT',
    'DB_ENGINE',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
]

for var in env_vars:
    value = os.environ.get(var)
    if value is None:
        print(f"\033[91m✗ AUSENTE\033[0m - {var}")
        all_passed = False
    elif var == 'DJANGO_SECRET_KEY' and value == 'sua-chave-secreta-gerada-para-producao':
        print(f"\033[91m✗ PADRÃO\033[0m - {var} (usando valor padrão)")
        all_passed = False
    elif var == 'DB_PASSWORD' and value in ('', 'sua_senha_segura_db'):
        print(f"\033[91m✗ INSEGURO\033[0m - {var} (usando senha fraca ou padrão)")
        all_passed = False
    else:
        print(f"\033[92m✓ OK\033[0m - {var}")

print("\n== RESULTADO FINAL ==\n")
if all_passed:
    print("\033[92m✓ SUCESSO!\033[0m O ambiente parece estar configurado corretamente para produção.")
else:
    print("\033[91m✗ ATENÇÃO!\033[0m Foram detectados problemas na configuração de produção.")
    print("Por favor, corrija os problemas indicados antes de implantar em produção.")

print("\nObrigado por usar o verificador de ambiente de produção!") 