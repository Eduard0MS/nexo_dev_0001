# Configuração do Ambiente de Produção

Este documento explica como configurar e implantar corretamente o projeto Nexo em um ambiente de produção seguro.

## Pré-requisitos

- Python 3.8 ou superior
- PostgreSQL (recomendado para produção)
- Servidor web (Nginx ou Apache)
- Certificado SSL (Let's Encrypt ou similar)

## 1. Instalação das Dependências

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

## 2. Configuração do Ambiente

### 2.1. Arquivo .env

Crie ou atualize o arquivo `.env` na raiz do projeto com as seguintes variáveis:

```ini
# Ambiente
DJANGO_ENVIRONMENT=production

# Configurações Django
DJANGO_SECRET_KEY=sua-chave-secreta-gerada-para-producao
DJANGO_ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DJANGO_DEBUG=False

# Banco de dados PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=nexus_prod
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_segura_db
DB_HOST=localhost
DB_PORT=5432

# Credenciais OAuth
GOOGLE_CLIENT_ID=seu-client-id-do-google
GOOGLE_CLIENT_SECRET=seu-client-secret-do-google
MICROSOFT_CLIENT_ID=seu-client-id-da-microsoft
MICROSOFT_CLIENT_SECRET=seu-client-secret-da-microsoft

# Configurações de Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# Configurações de Cache Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Configurações de Backup
BACKUP_ENCRYPTION_KEY=sua-chave-de-criptografia-backup
```

### 2.2. Gerar SECRET_KEY

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## 3. Configuração do Banco de Dados

### 3.1. PostgreSQL

```bash
# Instalar PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Criar usuário e banco
sudo -u postgres psql
CREATE DATABASE nexus_prod;
CREATE USER seu_usuario_db WITH PASSWORD 'sua_senha_segura_db';
GRANT ALL PRIVILEGES ON DATABASE nexus_prod TO seu_usuario_db;
\q
```

### 3.2. Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

## 4. Configuração OAuth

### 4.1. Google OAuth

1. Acesse [Google Console](https://console.developers.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google+ e Google OAuth2
4. Crie credenciais OAuth 2.0
5. Configure os URIs de redirecionamento:
   - `https://seu-dominio.com/accounts/google/login/callback/`
6. Anote o `Client ID` e `Client Secret`

### 4.2. Microsoft OAuth

1. Acesse [Azure Portal](https://portal.azure.com/)
2. Registre uma nova aplicação
3. Configure permissões da API
4. Configure URIs de redirecionamento
5. Anote o `Application ID` e `Client Secret`

### 4.3. Configurar no Django

Execute o script:

```bash
python scripts/oauth/setup_social_app.py
```

## 5. Configuração do Servidor Web

### 5.1. Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Testar configuração
gunicorn --config gunicorn_config.py config.wsgi:application
```

### 5.2. Nginx

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/projeto/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/projeto/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

## 6. Segurança

### 6.1. Firewall

```bash
# UFW básico
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 6.2. SSL/TLS

```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

### 6.3. Backup Automático

Configure o cron para backup automático:

```bash
# Editar crontab
crontab -e

# Adicionar linha para backup diário às 2h
0 2 * * * cd /path/to/projeto && python scripts/security/backup.py
```

### 6.4. Monitoramento Anti-Ransomware

```bash
# Executar em background
nohup python scripts/security/ransomware_monitor.py &
```

## 7. Verificação de Produção

Antes de colocar em produção, execute:

```bash
python scripts/security/check_production.py
```

## 8. Deploy

### 8.1. Systemd Service

Crie `/etc/systemd/system/nexo.service`:

```ini
[Unit]
Description=Nexo Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/projeto
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --config gunicorn_config.py config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8.2. Ativar e iniciar

```bash
sudo systemctl daemon-reload
sudo systemctl enable nexo
sudo systemctl start nexo
sudo systemctl status nexo
```

## 9. Monitoramento

### 9.1. Logs

```bash
# Logs do Gunicorn
tail -f logs/gunicorn-error.log
tail -f logs/gunicorn-access.log

# Logs do sistema
sudo journalctl -u nexo -f
```

### 9.2. Status

```bash
# Verificar status do serviço
sudo systemctl status nexo

# Verificar portas
sudo netstat -tlnp | grep :8000
```

## 10. Manutenção

### 10.1. Atualizações

```bash
# Backup antes da atualização
python scripts/security/backup.py

# Atualizar código
git pull origin main

# Atualizar dependências
pip install -r requirements.txt

# Aplicar migrations
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviço
sudo systemctl restart nexo
```

### 10.2. Restaurar Backup

```bash
python scripts/security/backup.py --restore backup_YYYYMMDD_HHMMSS.tar.gz
```

## 🔐 Checklist de Segurança

- [ ] SECRET_KEY única e segura
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configurado
- [ ] HTTPS configurado
- [ ] Certificados SSL válidos
- [ ] Firewall configurado
- [ ] Banco de dados PostgreSQL
- [ ] Backup automático configurado
- [ ] Monitoramento anti-ransomware ativo
- [ ] Logs configurados
- [ ] Credenciais OAuth configuradas
- [ ] Variáveis de ambiente protegidas

## 🆘 Suporte

Em caso de problemas:

1. Verifique os logs: `tail -f logs/gunicorn-error.log`
2. Execute verificação: `python scripts/security/check_production.py`
3. Consulte a documentação: `docs/production/`