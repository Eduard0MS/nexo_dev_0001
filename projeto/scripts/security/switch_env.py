#!/usr/bin/env python
"""
Script para alternar entre ambientes de desenvolvimento e produção
Facilita a mudança de configurações no arquivo .env
"""

import os
import sys
import shutil
from datetime import datetime

def backup_env():
    """Fazer backup do arquivo .env atual"""
    if os.path.exists('.env'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'.env.backup_{timestamp}'
        shutil.copy('.env', backup_file)
        print(f"📋 Backup criado: {backup_file}")
        return backup_file
    return None

def show_status():
    """Mostrar status atual do ambiente"""
    print("🔍 Status do Ambiente")
    print("=" * 30)
    
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        return
    
    with open('.env', 'r') as f:
        content = f.read()
    
    # Verificar variáveis importantes
    lines = content.split('\n')
    config = {}
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
    
    # Mostrar configurações
    environment = config.get('DJANGO_ENVIRONMENT', 'Não definido')
    debug = config.get('DJANGO_DEBUG', 'Não definido')
    allowed_hosts = config.get('DJANGO_ALLOWED_HOSTS', 'Não definido')
    db_engine = config.get('DB_ENGINE', 'Não definido')
    
    print(f"🔧 Ambiente: {environment}")
    print(f"🐛 Debug: {debug}")
    print(f"🌐 Allowed Hosts: {allowed_hosts}")
    print(f"🗄️  Banco: {db_engine}")
    
    if environment == 'production':
        print("🔒 Modo: PRODUÇÃO")
        print("⚠️  Certifique-se de que todas as configurações estão corretas!")
    else:
        print("🛠️  Modo: DESENVOLVIMENTO")

def create_env_template(environment='development'):
    """Criar template do arquivo .env"""
    if environment == 'development':
        template = """# Configurações de Desenvolvimento
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=django-insecure-dev-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados SQLite (desenvolvimento)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# OAuth (desenvolvimento)
GOOGLE_CLIENT_ID=your-dev-google-client-id
GOOGLE_CLIENT_SECRET=your-dev-google-client-secret
MICROSOFT_CLIENT_ID=your-dev-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-dev-microsoft-client-secret

# Configurações opcionais
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
"""
    else:  # production
        template = """# Configurações de Produção
DJANGO_ENVIRONMENT=production
DJANGO_SECRET_KEY=ALTERE-PARA-UMA-CHAVE-SECRETA-SEGURA
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Banco de dados PostgreSQL (produção)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=nexus_prod
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_segura_db
DB_HOST=localhost
DB_PORT=5432

# OAuth (produção)
GOOGLE_CLIENT_ID=seu-client-id-google-producao
GOOGLE_CLIENT_SECRET=seu-client-secret-google-producao
MICROSOFT_CLIENT_ID=seu-client-id-microsoft-producao
MICROSOFT_CLIENT_SECRET=seu-client-secret-microsoft-producao

# Configurações de segurança
BACKUP_ENCRYPTION_KEY=sua-chave-de-criptografia-backup

# Email (produção)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@dominio.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# Cache Redis (opcional)
REDIS_URL=redis://localhost:6379/0
"""
    
    return template

def switch_to_development():
    """Alternar para ambiente de desenvolvimento"""
    print("🛠️  Configurando ambiente de DESENVOLVIMENTO...")
    
    # Backup atual
    backup_file = backup_env()
    
    # Criar arquivo .env para desenvolvimento
    template = create_env_template('development')
    
    with open('.env', 'w') as f:
        f.write(template)
    
    print("✅ Arquivo .env configurado para desenvolvimento")
    print("\n📝 Configurações aplicadas:")
    print("- DEBUG = True")
    print("- Banco SQLite")
    print("- Allowed Hosts: localhost, 127.0.0.1")
    print("- OAuth para localhost")
    
    print("\n⚠️  IMPORTANTE:")
    print("- Configure suas credenciais OAuth no arquivo .env")
    print("- Execute: python manage.py migrate")
    print("- Execute: python scripts/oauth/setup_social_app.py")

def switch_to_production():
    """Alternar para ambiente de produção"""
    print("🔒 Configurando ambiente de PRODUÇÃO...")
    
    # Verificar se já existe configuração
    if os.path.exists('.env'):
        response = input("⚠️  Arquivo .env existe. Substituir? (s/N): ")
        if response.lower() != 's':
            print("❌ Operação cancelada")
            return
    
    # Backup atual
    backup_file = backup_env()
    
    # Criar arquivo .env para produção
    template = create_env_template('production')
    
    with open('.env', 'w') as f:
        f.write(template)
    
    print("✅ Arquivo .env configurado para produção")
    print("\n📝 Configurações aplicadas:")
    print("- DEBUG = False")
    print("- Banco PostgreSQL")
    print("- HTTPS obrigatório")
    print("- Configurações de segurança rigorosas")
    
    print("\n🚨 OBRIGATÓRIO - Configure antes de usar:")
    print("1. DJANGO_SECRET_KEY - gere uma chave única")
    print("2. DJANGO_ALLOWED_HOSTS - seu domínio real")
    print("3. Credenciais do banco PostgreSQL")
    print("4. Credenciais OAuth de produção")
    print("5. BACKUP_ENCRYPTION_KEY - para backups seguros")
    
    print("\n✅ Próximos passos:")
    print("- Edite o arquivo .env com suas configurações reais")
    print("- Execute: python scripts/security/check_production.py")
    print("- Execute: python manage.py migrate")
    print("- Execute: python scripts/oauth/setup_social_app.py")

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("🔧 Gerenciador de Ambientes - Nexo")
        print("=" * 40)
        print("Uso: python scripts/security/switch_env.py [comando]")
        print("\nComandos disponíveis:")
        print("  status    - Mostrar ambiente atual")
        print("  dev       - Configurar para desenvolvimento")
        print("  prod      - Configurar para produção")
        print("\nExemplos:")
        print("  python scripts/security/switch_env.py status")
        print("  python scripts/security/switch_env.py dev")
        print("  python scripts/security/switch_env.py prod")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_status()
    elif command == 'dev' or command == 'development':
        switch_to_development()
    elif command == 'prod' or command == 'production':
        switch_to_production()
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("Comandos válidos: status, dev, prod")

if __name__ == "__main__":
    main()