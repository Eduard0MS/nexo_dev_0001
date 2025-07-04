"""
Configuração do Gunicorn para ambiente de produção
"""

import multiprocessing

# Arquivo WSGI específico para produção
wsgi_app = 'Nexus.wsgi_prod:application'

# Número de workers: recomendação (2 x número de núcleos) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Tipo de worker (usar gevent para melhor performance com muitas conexões)
worker_class = 'gevent'

# Porta e binding
bind = '0.0.0.0:8000'

# Timeout (em segundos)
timeout = 120

# Configurações de log
accesslog = 'logs/gunicorn-access.log'
errorlog = 'logs/gunicorn-error.log'
loglevel = 'info'

# Recarrega automaticamente quando o código é alterado?
reload = False  # Desativado em produção

# Limite de conexões
max_requests = 1000
max_requests_jitter = 50

# Timeout de conexão
keepalive = 5 