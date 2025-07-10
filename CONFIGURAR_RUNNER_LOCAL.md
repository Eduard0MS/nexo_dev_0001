# 🏠 Configurar Self-Hosted Runner GitHub Actions

## Por que usar Self-Hosted Runner?

O GitHub Actions hospedado não consegue acessar redes privadas (IP 10.209.15.176).
Um runner local resolve o problema executando os jobs diretamente na VM.

## 🔧 Configuração (5 minutos)

### 1. Baixar o Runner
```bash
cd /home/eduardo/Documentos/nexo
mkdir actions-runner && cd actions-runner

# Baixar runner para Linux x64
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
```

### 2. Configurar o Runner
```bash
# Configurar (você precisará de um token do GitHub)
./config.sh --url https://github.com/Eduard0MS/nexo_dev_0001 --token YOUR_TOKEN
```

**Para obter o token:**
1. Vá para: https://github.com/Eduard0MS/nexo_dev_0001/settings/actions/runners
2. Clique em "New self-hosted runner"
3. Escolha "Linux" e copie os comandos

### 3. Instalar como Serviço
```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

### 4. Atualizar Workflow
No arquivo `.github/workflows/ci-cd.yml`, mudar:
```yaml
jobs:
  build-and-deploy:
    runs-on: self-hosted  # Em vez de ubuntu-latest
```

## ✅ Vantagens
- ✅ Acesso direto à rede local
- ✅ Deploy instantâneo (sem SSH)
- ✅ Controle total do ambiente
- ✅ Sem problemas de conectividade

## 🎯 Resultado
Deploy automático funcionará perfeitamente na sua VM local! 