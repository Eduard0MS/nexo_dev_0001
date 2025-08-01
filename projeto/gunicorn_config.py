"""
Configuração do Gunicorn para ambiente de produção do Nexo
"""

import multiprocessing
import os

# Arquivo WSGI específico para produção
wsgi_app = "config.wsgi:application"

# Número de workers: recomendação (2 x número de núcleos) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Tipo de worker (usar sync padrão)
worker_class = "sync"

# Porta e binding
bind = "127.0.0.1:8000"

# Timeout (em segundos)
timeout = 120

# Configurações de log
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Recarrega automaticamente quando o código é alterado?
reload = False  # Desativado em produção

# Limite de conexões
max_requests = 1000
max_requests_jitter = 50

# Timeout de conexão
keepalive = 5

# User e group (em produção, usar usuário específico)
# user = "www-data"
# group = "www-data"

# PID file
pidfile = "logs/gunicorn.pid"

# Configurações de workers
worker_connections = 1000
max_requests_jitter = 50

# Preload da aplicação (melhora performance)
preload_app = True

# Timeout para graceful workers restart
graceful_timeout = 30

# Configurações de SSL (se necessário)
# keyfile = "/path/to/ssl/private.key"
# certfile = "/path/to/ssl/certificate.crt"

# Configurações de logging avançadas
capture_output = True
enable_stdio_inheritance = True

# Configurações de limite de memória
# max_requests_jitter ajuda a prevenir que todos os workers reiniciem ao mesmo tempo
worker_tmp_dir = "/dev/shm"  # Usar RAM para melhor performance

# Hooks customizados
def on_starting(server):
    """Executado quando o Gunicorn está iniciando"""
    server.log.info("🚀 Nexo está iniciando...")

def on_reload(server):
    """Executado quando o Gunicorn está recarregando"""
    server.log.info("🔄 Nexo está recarregando...")

def worker_int(worker):
    """Executado quando um worker é interrompido"""
    worker.log.info(f"🛑 Worker {worker.pid} foi interrompido")

def pre_fork(server, worker):
    """Executado antes de fazer fork do worker"""
    server.log.info(f"🔀 Fazendo fork do worker {worker.pid}")

def post_fork(server, worker):
    """Executado após fazer fork do worker"""
    server.log.info(f"✅ Worker {worker.pid} iniciado")

def when_ready(server):
    """Executado quando o servidor está pronto"""
    server.log.info("✅ Nexo está pronto para receber conexões!")

def worker_abort(worker):
    """Executado quando um worker é abortado"""
    worker.log.info(f"💀 Worker {worker.pid} foi abortado")

# Configurações específicas por ambiente
environment = os.environ.get("DJANGO_ENVIRONMENT", "development")

if environment == "production":
    # Configurações de produção
    workers = multiprocessing.cpu_count() * 2 + 1
    timeout = 120
    keepalive = 5
    max_requests = 1000
    preload_app = True
    reload = False
    loglevel = "info"
else:
    # Configurações de desenvolvimento
    workers = 2
    timeout = 60
    keepalive = 2
    max_requests = 0  # Sem limite para desenvolvimento
    preload_app = False
    reload = True
    loglevel = "debug" 