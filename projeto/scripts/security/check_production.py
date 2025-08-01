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
if not os.path.exists(".env"):
    print("ERRO: Arquivo .env não encontrado!")
    print("Por favor, crie um arquivo .env com as configurações de produção.")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_ENVIRONMENT", "production")
django.setup()

from django.conf import settings

# Lista de verificações
checks = [
    ("DEBUG está desativado", not settings.DEBUG),
    (
        "ALLOWED_HOSTS está configurado",
        len(settings.ALLOWED_HOSTS) > 0 and settings.ALLOWED_HOSTS != ["*"],
    ),
    ("SECRET_KEY foi alterada", settings.SECRET_KEY != "django-insecure-..."),
    ("HTTPS está configurado", getattr(settings, 'SECURE_SSL_REDIRECT', False)),
    ("HSTS está configurado", getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0),
    (
        "Cookies seguros estão configurados",
        getattr(settings, 'SESSION_COOKIE_SECURE', False) and getattr(settings, 'CSRF_COOKIE_SECURE', False),
    ),
    (
        "Cookies HTTP-only estão configurados",
        getattr(settings, 'SESSION_COOKIE_HTTPONLY', False) and getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
    ),
    ("Diretório de logs existe", os.path.isdir("logs")),
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
db_config = settings.DATABASES["default"]
if db_config["ENGINE"] == "django.db.backends.sqlite3":
    print("\033[91m✗ AVISO: Usando SQLite em produção!\033[0m")
    print(
        "Recomendamos usar PostgreSQL, MySQL ou outro banco de dados adequado para produção."
    )
    all_passed = False
else:
    print(f"\033[92m✓ OK\033[0m - Usando {db_config['ENGINE']}")

print("\n== VARIÁVEIS DE AMBIENTE CRÍTICAS ==\n")
env_vars = [
    "DJANGO_SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_ENVIRONMENT",
    "DB_ENGINE",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
]

for var in env_vars:
    value = os.environ.get(var)
    if value:
        # Não mostrar valores sensíveis
        if "SECRET" in var or "PASSWORD" in var:
            display_value = "***DEFINIDO***"
        else:
            display_value = value[:20] + "..." if len(value) > 20 else value
            
        # Verificações específicas
        if var == "DJANGO_SECRET_KEY" and value == "sua-chave-secreta-gerada-para-producao":
            print(f"\033[91m✗ FALHOU\033[0m - {var}: Usar uma chave real!")
            all_passed = False
        else:
            print(f"\033[92m✓ OK\033[0m - {var}: {display_value}")
    else:
        print(f"\033[91m✗ FALHOU\033[0m - {var}: Não definido")
        all_passed = False

print("\n== ARQUIVOS E DIRETÓRIOS ==\n")
required_files = [
    ("Arquivo de configuração do Gunicorn", "gunicorn_config.py"),
    ("Diretório de scripts", "scripts/"),
    ("Diretório de logs", "logs/"),
    ("Arquivo requirements.txt", "requirements.txt"),
]

for description, path in required_files:
    exists = os.path.exists(path)
    status = "✓ OK" if exists else "✗ FALHOU"
    color = "\033[92m" if exists else "\033[91m"
    print(f"{color}{status}\033[0m - {description}: {path}")
    if not exists:
        all_passed = False

print("\n== RESUMO ==\n")
if all_passed:
    print("\033[92m🎉 PARABÉNS! Todas as verificações passaram.\033[0m")
    print("O ambiente está pronto para produção.")
else:
    print("\033[91m❌ FALHOU! Existem problemas que precisam ser corrigidos.\033[0m")
    print("Corrija os itens marcados com ✗ antes de implantar em produção.")

print("\n== PRÓXIMOS PASSOS ==\n")
print("1. Corrigir todos os problemas apontados")
print("2. Executar: python manage.py collectstatic --noinput")
print("3. Executar: python manage.py migrate")
print("4. Configurar o servidor web (Nginx/Apache)")
print("5. Configurar certificados SSL")
print("6. Iniciar o Gunicorn")
print("7. Configurar monitoramento")
print("8. Configurar backup automático")

sys.exit(0 if all_passed else 1)