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
```

**Importante**: Gere uma chave secreta forte para `DJANGO_SECRET_KEY`. Você pode usar o seguinte comando:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2.2. Banco de Dados

Crie o banco de dados PostgreSQL:

```bash
sudo -u postgres psql
CREATE DATABASE nexus_prod;
CREATE USER seu_usuario_db WITH PASSWORD 'sua_senha_segura_db';
ALTER ROLE seu_usuario_db SET client_encoding TO 'utf8';
ALTER ROLE seu_usuario_db SET default_transaction_isolation TO 'read committed';
ALTER ROLE seu_usuario_db SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nexus_prod TO seu_usuario_db;
\q
```

### 2.3. Arquivos Estáticos e Migrações

```bash
# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

# Criar superusuário
python manage.py createsuperuser
```

## 3. Verificação do Ambiente de Produção

Execute o script de verificação para garantir que todas as configurações de produção estão corretas:

```bash
python check_production.py
```

Resolva quaisquer problemas reportados pelo script antes de continuar.

## 4. Configuração do Gunicorn

O Gunicorn é um servidor WSGI recomendado para produção. Use o arquivo de configuração fornecido:

```bash
# Iniciar o Gunicorn usando o arquivo de configuração
gunicorn -c gunicorn_config.py
```

Para garantir que o Gunicorn continue rodando, recomendamos configurá-lo como um serviço systemd.

### 4.1. Criar serviço systemd (Linux)

Crie um arquivo `/etc/systemd/system/nexo.service`:

```ini
[Unit]
Description=Nexo Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/caminho/para/nexo
ExecStart=/caminho/para/venv/bin/gunicorn -c gunicorn_config.py

[Install]
WantedBy=multi-user.target
```

Em seguida:

```bash
sudo systemctl daemon-reload
sudo systemctl start nexo
sudo systemctl enable nexo
```

## 5. Configuração do Nginx

O Nginx é recomendado como proxy reverso para o Gunicorn:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name seu-dominio.com www.seu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Arquivos estáticos
    location /static/ {
        alias /caminho/para/nexo/staticfiles/;
    }
    
    # Proxy para o Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Manutenção e Monitoramento

### 6.1. Backups Regulares

Configure backups diários do banco de dados:

```bash
# Adicione ao crontab
0 2 * * * pg_dump -U seu_usuario_db nexus_prod | gzip > /caminho/para/backups/nexus_$(date +\%Y\%m\%d).sql.gz
```

### 6.2. Monitoramento de Erros

Configure um sistema de monitoramento para alertá-lo sobre erros. Os logs do Django são armazenados em:

- `logs/django-errors.log` - Erros do Django
- `logs/gunicorn-error.log` - Erros do Gunicorn
- `logs/gunicorn-access.log` - Acessos ao Gunicorn

### 6.3. Atualizações de Segurança

Mantenha o sistema atualizado:

```bash
# Verificar atualizações de segurança
pip list --outdated

# Atualizar dependências
pip install --upgrade nome-do-pacote
```

## 7. Procedimento de Implantação

Para atualizar a aplicação em produção:

```bash
# 1. Ative o modo de manutenção (se disponível)

# 2. Faça backup do banco de dados
pg_dump -U seu_usuario_db nexus_prod | gzip > /caminho/para/backups/nexus_pre_deploy_$(date +\%Y\%m\%d).sql.gz

# 3. Puxe as alterações do repositório
git pull

# 4. Instale novas dependências
pip install -r requirements.txt

# 5. Aplique migrações
python manage.py migrate

# 6. Colete arquivos estáticos
python manage.py collectstatic --no-input

# 7. Reinicie o serviço
sudo systemctl restart nexo

# 8. Desative o modo de manutenção
```

## Conclusão

Seguindo estas instruções, você terá um ambiente de produção seguro e robusto para a aplicação Nexo. Em caso de dúvidas ou problemas, consulte a documentação do Django ou entre em contato com a equipe de desenvolvimento. 