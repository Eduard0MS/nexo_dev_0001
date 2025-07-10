# Guia de Configuração CI/CD - Nexo

## 🚀 Passos para Tornar o CI/CD Pronto para Uso

### 1. **Configurar Secrets no GitHub**

Vá para `Settings > Secrets and variables > Actions` no seu repositório GitHub e adicione:

```
SECRET_KEY=sua-secret-key-django-super-secreta-aqui
DATABASE_URL=postgresql://postgres:password@localhost:5432/nexo_prod
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,localhost,127.0.0.1
GOOGLE_CLIENT_ID=seu-google-client-id
GOOGLE_CLIENT_SECRET=seu-google-client-secret
MICROSOFT_CLIENT_ID=seu-microsoft-client-id  
MICROSOFT_CLIENT_SECRET=seu-microsoft-client-secret
```

### 2. **Gerar SECRET_KEY Segura**

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"
```

### 3. **Configurar Branch Protection**

No GitHub, vá para `Settings > Branches` e configure:
- ✅ Require pull request reviews
- ✅ Require status checks to pass: `test`, `security`
- ✅ Require up-to-date branches  
- ✅ Include administrators

### 4. **Ajustar Configurações de Banco de Dados**

O CI atualmente usa PostgreSQL, mas o projeto usa MySQL em desenvolvimento. Escolha uma das opções:

**Opção A: Unificar em PostgreSQL (Recomendado)**
```bash
# Instalar PostgreSQL
pip install psycopg2-binary

# Atualizar settings.py para usar PostgreSQL também em desenvolvimento
```

**Opção B: Manter MySQL mas ajustar CI**
- Alterar o workflow para usar MySQL em vez de PostgreSQL

### 5. **Implementar Scripts de Deploy**

Completar as seções de deploy no workflow:

```yaml
- name: Deploy to production
  if: github.ref == 'refs/heads/main'
  run: |
    echo "Deploying to production..."
    # Adicionar comandos de deploy reais aqui
    # Exemplo: rsync, ssh, docker deploy, etc.
```

### 6. **Configurar Notificações**

Adicionar webhook do Slack ou email:

```yaml
- name: Notify on success
  run: |
    curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"✅ Deploy realizado com sucesso!"}' \
    ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 7. **Validar Configuração**

Execute o script de verificação:

```bash
cd nexo_dev/nexo
python check_production.py
```

### 8. **Testar Pipeline Localmente**

```bash
# Executar todos os testes
python scripts/run_all_tests.py

# Verificar linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Verificar formatação
black --check --diff .

# Análise de segurança
bandit -r . --severity-level medium
safety check
```

## ✅ **Checklist Final - Sistema Pronto**

- [ ] Secrets configurados no GitHub
- [ ] Branch protection ativada
- [ ] Testes passando localmente
- [ ] Scripts de deploy implementados
- [ ] Notificações configuradas
- [ ] Configuração de produção validada
- [ ] Primeiro deploy de teste realizado

## 📋 **Status Atual**

**✅ Pronto:**
- Pipeline de CI completo
- Testes abrangentes
- Análise de qualidade e segurança
- Configurações de produção

**⚠️ Precisa de Configuração:**
- Secrets do GitHub
- Scripts de deploy efetivos
- Notificações
- Unificação de banco de dados (PostgreSQL vs MySQL)

## 🎯 **Próximos Passos Recomendados**

1. **Configurar secrets** (5 minutos)
2. **Unificar banco de dados** (15 minutos)
3. **Implementar deploy scripts** (30 minutos)
4. **Configurar notificações** (10 minutos)
5. **Testar pipeline completo** (15 minutos)

**Tempo total estimado para tornar pronto: ~75 minutos** 