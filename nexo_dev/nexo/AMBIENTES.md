# 🔧 Gerenciamento de Ambientes

Este documento explica como alternar entre os ambientes de desenvolvimento e produção.

## 📋 Resumo

O projeto usa a variável `DJANGO_ENVIRONMENT` no arquivo `.env` para determinar se está rodando em **desenvolvimento** ou **produção**.

## 🚀 Como usar

### Script Automático (Recomendado)

Use o script `switch_env.py` para alternar facilmente entre ambientes:

```bash
# Ver ambiente atual
python switch_env.py status

# Configurar para desenvolvimento
python switch_env.py dev

# Configurar para produção
python switch_env.py prod
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

### Produção (`production`)
- ❌ `DEBUG = False`
- ✅ Gunicorn + Nginx
- ✅ HTTPS obrigatório
- ✅ Configurações de segurança rigorosas
- ✅ Logs de erro em arquivo

## 📝 Checklist para Deploy

Antes de fazer deploy para produção:

1. **Alterar ambiente:**
   ```bash
   python switch_env.py prod
   ```

2. **Verificar configurações:**
   - `ALLOWED_HOSTS` configurado
   - `CSRF_TRUSTED_ORIGINS` configurado
   - Banco de dados configurado

3. **Reiniciar serviços:**
   ```bash
   sudo systemctl restart gunicorn
   sudo systemctl restart nginx
   ```

4. **Após deploy, voltar para desenvolvimento:**
   ```bash
   python switch_env.py dev
   ```

## ⚠️ Importante

- **SEMPRE** verifique o ambiente antes de fazer deploy
- **NUNCA** deixe `DEBUG = True` em produção
- **SEMPRE** volte para `development` após o deploy

## 🐛 Troubleshooting

### Erro 400 em desenvolvimento
- Verifique se `DJANGO_ENVIRONMENT=development`
- Reinicie o servidor Django

### Erro 400 em produção
- Verifique se `DJANGO_ENVIRONMENT=production`
- Verifique logs do Gunicorn: `sudo journalctl -u gunicorn`
- Verifique logs do Nginx: `sudo journalctl -u nginx` 