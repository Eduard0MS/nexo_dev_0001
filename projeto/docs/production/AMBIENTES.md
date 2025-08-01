# 🔧 Gerenciamento de Ambientes

Este documento explica como alternar entre os ambientes de desenvolvimento e produção.

## 📋 Resumo

O projeto usa a variável `DJANGO_ENVIRONMENT` no arquivo `.env` para determinar se está rodando em **desenvolvimento** ou **produção**.

## 🚀 Como usar

### Script Automático (Recomendado)

Use o script `scripts/security/switch_env.py` para alternar facilmente entre ambientes:

```bash
# Ver ambiente atual
python scripts/security/switch_env.py status

# Configurar para desenvolvimento
python scripts/security/switch_env.py dev

# Configurar para produção
python scripts/security/switch_env.py prod
```

### Manual

Edite o arquivo `.env` e altere a linha:
```bash
DJANGO_ENVIRONMENT=development  # Para desenvolvimento
DJANGO_ENVIRONMENT=production   # Para produção
```

## 🔄 Diferenças entre Ambientes

### Desenvolvimento (`development`)
- ✅ `DEBUG = True`
- ✅ Servidor de desenvolvimento Django
- ✅ Logs detalhados
- ✅ Sem HTTPS obrigatório
- ✅ Configurações de segurança relaxadas
- ✅ SQLite (padrão)
- ✅ OAuth localhost

### Produção (`production`)
- ❌ `DEBUG = False`
- ✅ Gunicorn + Nginx
- ✅ HTTPS obrigatório
- ✅ Configurações de segurança rigorosas
- ✅ Logs de erro em arquivo
- ✅ PostgreSQL
- ✅ OAuth domínio real

## 📝 Checklist para Deploy

### Antes do Deploy
- [ ] Arquivo `.env` atualizado com configurações de produção
- [ ] Banco PostgreSQL configurado
- [ ] Credenciais OAuth configuradas
- [ ] Certificados SSL instalados
- [ ] Firewall configurado
- [ ] Backup configurado

### Verificações
- [ ] `python scripts/security/check_production.py`
- [ ] Teste de OAuth
- [ ] Teste de HTTPS
- [ ] Teste de backup

### Pós-Deploy
- [ ] Monitoramento ativo
- [ ] Logs funcionando
- [ ] Backup automático
- [ ] Proteção anti-ransomware

## 🔧 Configurações por Ambiente

### `.env` para Desenvolvimento
```ini
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=django-insecure-dev-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite (padrão)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# OAuth localhost
GOOGLE_CLIENT_ID=your-dev-client-id
GOOGLE_CLIENT_SECRET=your-dev-client-secret
```

### `.env` para Produção
```ini
DJANGO_ENVIRONMENT=production
DJANGO_SECRET_KEY=sua-chave-secreta-super-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=nexus_prod
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_segura_db
DB_HOST=localhost
DB_PORT=5432

# OAuth produção
GOOGLE_CLIENT_ID=seu-client-id-producao
GOOGLE_CLIENT_SECRET=seu-client-secret-producao

# Configurações extras de segurança
BACKUP_ENCRYPTION_KEY=sua-chave-backup
```

## ⚠️ Avisos Importantes

1. **Nunca commite o `.env`** - adicione ao `.gitignore`
2. **SECRET_KEY única** para cada ambiente
3. **Backup antes** de alterar ambiente
4. **Teste sempre** após mudança de ambiente
5. **OAuth diferente** para cada ambiente

## 🛠️ Comandos Úteis

```bash
# Verificar ambiente atual
python manage.py shell -c "from django.conf import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Debug: {settings.DEBUG}')"

# Coletar arquivos estáticos (produção)
python manage.py collectstatic --noinput

# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Verificar configuração
python scripts/security/check_production.py
```