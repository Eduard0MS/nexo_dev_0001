# 🚀 Deploy Automático - Configuração

Este projeto está configurado para **deploy automático** sempre que você fizer push para a branch `main`.

## 📋 Pré-requisitos

### 1. Servidor de Produção
- ✅ Projeto Nexo rodando com `gunicorn_nexo`
- ✅ Git configurado no servidor
- ✅ Acesso SSH configurado
- ✅ Usuário com permissões sudo para `systemctl`

### 2. Secrets do GitHub
Configure estes secrets em: **Settings** → **Secrets and variables** → **Actions**

| Secret | Descrição | Exemplo |
|--------|-----------|---------|
| `PRODUCTION_HOST` | IP ou domínio do servidor | `123.456.789.10` ou `nexo.exemplo.com` |
| `PRODUCTION_USER` | Usuário SSH | `eduardo` |
| `PRODUCTION_SSH_KEY` | Chave SSH privada | Conteúdo completo da chave privada |
| `PRODUCTION_PROJECT_PATH` | Caminho do projeto | `/home/eduardo/nexo` |
| `PRODUCTION_VENV_PATH` | Caminho do venv (opcional) | `/home/eduardo/nexo/venv` |

## 🔐 Gerando Chave SSH

No seu **computador local**:
```bash
# Gerar nova chave SSH para deploy
ssh-keygen -t rsa -b 4096 -C "deploy-nexo" -f ~/.ssh/nexo_deploy

# Copiar chave pública para o servidor
ssh-copy-id -i ~/.ssh/nexo_deploy.pub eduardo@SEU_SERVIDOR

# Copiar chave privada para o GitHub Secret
cat ~/.ssh/nexo_deploy
```

## ⚙️ Configuração do Servidor

### 1. Permissões Sudo sem Senha
No servidor, adicione ao `/etc/sudoers`:
```bash
# Permitir restart do gunicorn sem senha
eduardo ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn_nexo
eduardo ALL=(ALL) NOPASSWD: /bin/systemctl status gunicorn_nexo
eduardo ALL=(ALL) NOPASSWD: /bin/systemctl is-active gunicorn_nexo
```

### 2. Estrutura do Projeto
```
/home/eduardo/
├── nexo/                    # Projeto principal
│   ├── manage.py
│   ├── requirements.txt
│   └── venv/               # Ambiente virtual
└── backup_YYYYMMDD_HHMMSS/ # Backups automáticos
```

## 🎯 Como Funciona

### Fluxo Automático
1. **Push para main** → Pipeline inicia
2. **Testes** → Validação de código e segurança
3. **Deploy** → SSH no servidor + comandos automáticos
4. **Verificação** → Saúde da aplicação
5. **Notificação** → Resultado do deploy

### Comandos Executados no Servidor
```bash
cd /caminho/projeto
git reset --hard origin/main  # Atualizar código
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn_nexo
```

## 🔍 Monitoramento

### Logs do Deploy
- Acompanhe em: **Actions** tab no GitHub
- Logs detalhados de cada etapa
- Notificações de sucesso/falha

### Verificações Automáticas
- ✅ Status do serviço `gunicorn_nexo`
- ✅ Teste de saúde HTTP
- ✅ Backup automático antes do deploy

## 🚨 Resolução de Problemas

### Deploy Falha
1. Verificar logs no GitHub Actions
2. Checar SSH e permissões
3. Validar caminhos dos secrets
4. Testar conexão manual: `ssh usuario@servidor`

### Rollback Manual
```bash
cd /home/eduardo
sudo systemctl stop gunicorn_nexo
rm -rf nexo
mv backup_YYYYMMDD_HHMMSS nexo
sudo systemctl start gunicorn_nexo
```

## 🎉 Primeiro Deploy

1. Configure todos os secrets
2. Faça um push pequeno para `main`
3. Acompanhe o deploy no GitHub Actions
4. Acesse sua aplicação para verificar

---

**🔧 Configurado por**: Pipeline CI/CD Nexo  
**📅 Data**: $(date)  
**🎯 Objetivo**: Deploy automático e seguro 