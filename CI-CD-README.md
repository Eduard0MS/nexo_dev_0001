# CI/CD Pipeline para o Projeto Nexo

Este documento descreve como configurar e usar o pipeline de CI/CD (Continuous Integration/Continuous Deployment) para o projeto Nexo usando GitHub Actions.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Configuração Inicial](#configuração-inicial)
- [Pipeline de CI/CD](#pipeline-de-cicd)
- [Deployment](#deployment)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)

## 🔎 Visão Geral

O pipeline de CI/CD está configurado para:

1. **Continuous Integration (CI):**
   - Executar testes automatizados
   - Verificar qualidade do código (linting)
   - Verificar formatação (Black)
   - Análise de segurança (Bandit, Safety)
   - Cobertura de testes

2. **Continuous Deployment (CD):**
   - Deploy automático para staging (branch `develop`)
   - Deploy automático para produção (branch `main`)
   - Containerização com Docker
   - Orquestração com Docker Compose

## ⚙️ Configuração Inicial

### 1. Configurar Secrets no GitHub

Vá para `Settings > Secrets and variables > Actions` no seu repositório GitHub e adicione:

```
SECRET_KEY=sua-secret-key-django-super-secreta
DATABASE_URL=postgresql://user:password@host:port/database
ALLOWED_HOSTS=seu-dominio.com,localhost
WEBHOOK_URL=https://hooks.slack.com/services/... (opcional)
```

### 2. Configurar Branch Protection

No GitHub, vá para `Settings > Branches` e configure:

- **Require pull request reviews**: Ativado
- **Require status checks**: Ativado
  - Selecione: `test`, `security`
- **Require up-to-date branches**: Ativado
- **Include administrators**: Ativado

### 3. Configurar Ambiente de Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/Eduard0MS/nexo_dev_0001.git
cd nexo_dev_0001

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependências
cd nexo_dev/nexo
pip install -r requirements.txt

# Configurar banco de dados local
python manage.py migrate
python manage.py collectstatic

# Executar testes
python manage.py test
```

## 🚀 Pipeline de CI/CD

### Fluxo de Trabalho

```mermaid
graph TD
    A[Push/PR] --> B[Checkout Code]
    B --> C[Setup Python]
    C --> D[Install Dependencies]
    D --> E[Linting & Format Check]
    E --> F[Run Tests]
    F --> G[Security Scan]
    G --> H{Branch?}
    H -->|develop| I[Deploy to Staging]
    H -->|main| J[Deploy to Production]
    H -->|other| K[End]
    I --> L[Health Check]
    J --> L
    L --> M[Notify Team]
```

### Jobs do Pipeline

1. **Test Job:**
   - Setup do ambiente Python 3.12
   - Instalação de dependências
   - Linting com flake8
   - Verificação de formatação com Black
   - Execução de testes Django
   - Cobertura de testes

2. **Security Job:**
   - Análise de código com Bandit
   - Verificação de vulnerabilidades com Safety

3. **Build and Deploy Job:**
   - Criação do pacote de deployment
   - Deploy para staging/produção
   - Upload de artefatos

4. **Notify Job:**
   - Notificações de sucesso/falha

### Comandos Úteis

```bash
# Executar pipeline localmente (simulado)
./scripts/run-ci-local.sh

# Deploy manual
./scripts/deploy.sh production

# Verificar logs
docker-compose logs -f web

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🐳 Docker & Containerização

### Desenvolvimento Local

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Executar comando no container
docker-compose exec web python manage.py shell

# Executar migrações
docker-compose exec web python manage.py migrate

# Parar serviços
docker-compose down
```

### Produção

```bash
# Build e deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde dos serviços
docker-compose ps
```

## 📊 Monitoramento

### Health Checks

O sistema inclui health checks automáticos:

- **Aplicação Django**: `http://localhost:8000/health/`
- **Banco de dados**: Verificação de conexão PostgreSQL
- **Redis**: Verificação de conectividade

### Logs

```bash
# Logs da aplicação
docker-compose logs web

# Logs do banco
docker-compose logs db

# Logs do Nginx
docker-compose logs nginx

# Logs do sistema (produção)
sudo journalctl -u nexo-gunicorn -f
```

### Métricas

Implemente monitoramento adicional com:

- **Prometheus + Grafana**: Métricas de performance
- **Sentry**: Monitoramento de erros
- **New Relic/DataDog**: APM completo

## 🔧 Troubleshooting

### Problemas Comuns

**1. Falha no Build**
```bash
# Verificar logs do GitHub Actions
# Ir para Actions > [workflow] > [job] > View logs

# Verificar localmente
docker-compose build web
```

**2. Falha nos Testes**
```bash
# Executar testes localmente
python manage.py test --verbosity=2

# Com cobertura
coverage run --source='.' manage.py test
coverage report
```

**3. Falha no Deploy**
```bash
# Verificar status dos serviços
systemctl status nexo-gunicorn
systemctl status nginx

# Verificar logs
sudo journalctl -u nexo-gunicorn --since "10 minutes ago"
```

**4. Problemas de Conectividade**
```bash
# Verificar rede Docker
docker network ls
docker network inspect nexo_default

# Verificar DNS
docker-compose exec web nslookup db
```

### Rollback

```bash
# Rollback automático (produção)
./scripts/rollback.sh

# Rollback manual
git revert HEAD
git push origin main
```

## 📝 Boas Práticas

### Development

1. **Sempre trabalhe em branches feature**
   ```bash
   git checkout -b feature/nova-funcionalidade
   git push -u origin feature/nova-funcionalidade
   ```

2. **Execute testes antes de fazer push**
   ```bash
   python manage.py test
   flake8 .
   black --check .
   ```

3. **Mantenha commits pequenos e descritivos**
   ```bash
   git commit -m "feat: adicionar sistema de relatórios"
   git commit -m "fix: corrigir bug no organograma"
   ```

### Production

1. **Sempre faça backup antes do deploy**
2. **Monitore logs após deploy**
3. **Tenha um plano de rollback**
4. **Use variáveis de ambiente para configurações**

### Security

1. **Nunca commite secrets no código**
2. **Use GitHub Secrets para variáveis sensíveis**
3. **Mantenha dependências atualizadas**
4. **Execute análise de segurança regularmente**

## 🔗 Links Úteis

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)

---

**Suporte**: Em caso de problemas, verifique os logs primeiro e consulte a documentação. Para ajuda adicional, abra uma issue no repositório. 