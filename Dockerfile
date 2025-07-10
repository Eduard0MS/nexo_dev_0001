# Dockerfile para o Projeto Nexo
FROM python:3.12-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SETTINGS_MODULE=Nexus.settings

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r nexo && useradd -r -g nexo nexo

# Criar diretórios da aplicação
WORKDIR /app
RUN mkdir -p /app/logs /app/media /app/static \
    && chown -R nexo:nexo /app

# Copiar requirements e instalar dependências Python
COPY nexo_dev/nexo/requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY nexo_dev/nexo/ /app/
RUN chown -R nexo:nexo /app

# Mudar para usuário não-root
USER nexo

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "Nexus.wsgi:application"] 