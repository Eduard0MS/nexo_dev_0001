#!/bin/bash

# Script de Deploy para o Projeto Nexo
# Uso: ./deploy.sh [staging|production]

set -e  # Parar em caso de erro

ENVIRONMENT=${1:-staging}
PROJECT_DIR="/var/www/nexo"
BACKUP_DIR="/var/backups/nexo"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Iniciando deploy para $ENVIRONMENT..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está rodando como usuário correto
if [ "$EUID" -eq 0 ]; then
    log_error "Não execute este script como root!"
    exit 1
fi

# Verificar se o ambiente é válido
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    log_error "Ambiente deve ser 'staging' ou 'production'"
    exit 1
fi

# Função para fazer backup
backup_application() {
    log_info "Criando backup da aplicação..."
    
    # Criar diretório de backup se não existir
    sudo mkdir -p "$BACKUP_DIR"
    
    # Backup do código
    if [ -d "$PROJECT_DIR" ]; then
        sudo tar -czf "$BACKUP_DIR/nexo-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$PROJECT_DIR" .
        log_info "Backup criado em $BACKUP_DIR"
    fi
    
    # Backup do banco de dados
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Fazendo backup do banco de dados..."
        # Ajuste conforme seu banco de dados
        sudo -u postgres pg_dump nexo_prod > "$BACKUP_DIR/db-backup-$(date +%Y%m%d-%H%M%S).sql"
    fi
}

# Função para atualizar código
update_code() {
    log_info "Atualizando código da aplicação..."
    
    cd "$PROJECT_DIR"
    
    # Fazer pull das mudanças
    git fetch origin
    git reset --hard origin/main
    
    # Atualizar submódulos se houver
    git submodule update --init --recursive
}

# Função para atualizar dependências
update_dependencies() {
    log_info "Atualizando dependências Python..."
    
    cd "$PROJECT_DIR"
    
    # Ativar ambiente virtual
    source "$VENV_DIR/bin/activate"
    
    # Atualizar pip e instalar dependências
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "Dependências atualizadas"
}

# Função para executar migrações
run_migrations() {
    log_info "Executando migrações do banco de dados..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Verificar migrações pendentes
    python manage.py showmigrations --plan
    
    # Executar migrações
    python manage.py migrate --noinput
    
    log_info "Migrações executadas com sucesso"
}

# Função para coletar arquivos estáticos
collect_static() {
    log_info "Coletando arquivos estáticos..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    python manage.py collectstatic --noinput --clear
    
    log_info "Arquivos estáticos coletados"
}

# Função para reiniciar serviços
restart_services() {
    log_info "Reiniciando serviços..."
    
    # Reiniciar Gunicorn
    sudo systemctl restart nexo-gunicorn
    
    # Reiniciar Nginx
    sudo systemctl restart nginx
    
    # Verificar status dos serviços
    if systemctl is-active --quiet nexo-gunicorn; then
        log_info "Gunicorn reiniciado com sucesso"
    else
        log_error "Falha ao reiniciar Gunicorn"
        exit 1
    fi
    
    if systemctl is-active --quiet nginx; then
        log_info "Nginx reiniciado com sucesso"
    else
        log_error "Falha ao reiniciar Nginx"
        exit 1
    fi
}

# Função para verificar saúde da aplicação
health_check() {
    log_info "Verificando saúde da aplicação..."
    
    # Aguardar um pouco para os serviços iniciarem
    sleep 5
    
    # Verificar se a aplicação está respondendo
    if curl -f -s -o /dev/null http://localhost/health/; then
        log_info "✅ Aplicação está funcionando corretamente"
    else
        log_error "❌ Aplicação não está respondendo"
        log_warn "Verifique os logs: sudo journalctl -u nexo-gunicorn -f"
        exit 1
    fi
}

# Função para limpeza pós-deploy
cleanup() {
    log_info "Limpando arquivos temporários..."
    
    cd "$PROJECT_DIR"
    
    # Remover arquivos .pyc
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Remover logs antigos (mais de 30 dias)
    find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_info "Limpeza concluída"
}

# Função principal de deploy
main() {
    log_info "Deploy para ambiente: $ENVIRONMENT"
    
    # Verificar se existe um deploy anterior
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Diretório do projeto não encontrado: $PROJECT_DIR"
        exit 1
    fi
    
    # Executar etapas do deploy
    backup_application
    update_code
    update_dependencies
    run_migrations
    collect_static
    restart_services
    health_check
    cleanup
    
    log_info "🎉 Deploy concluído com sucesso!"
    log_info "Aplicação disponível em: http://$(hostname)/nexo/"
}

# Executar deploy
main

# Enviar notificação (opcional)
if command -v curl &> /dev/null; then
    # Exemplo de webhook para Slack/Discord
    # curl -X POST -H 'Content-type: application/json' \
    #     --data '{"text":"✅ Deploy do Nexo concluído com sucesso em '"$ENVIRONMENT"'!"}' \
    #     $WEBHOOK_URL
    log_info "Deploy finalizado às $(date)"
fi 