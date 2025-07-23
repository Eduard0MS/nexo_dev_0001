#!/bin/bash
# 🚀 Deploy Local Automático - Nexo (Puramente Local)

echo "🚀 DEPLOY LOCAL INICIADO"
echo "========================"

# Navegar para diretório do projeto
cd /home/eduardo/Documentos/nexo/nexo_dev_0001

echo "🔄 Sincronizando arquivos locais..."
# Sincronizar arquivos da estrutura projeto/ para nexo_dev/ (se necessário)
if [ -d "./projeto/apps/core/static/" ]; then
    rsync -av --delete ./projeto/apps/core/static/ ./nexo_dev/nexo/core/static/
    echo "✅ Arquivos estáticos sincronizados"
fi
echo "✅ Arquivos locais verificados"

# Navegar para Django
cd nexo_dev/nexo

echo "📦 Ativando ambiente virtual..."
source /home/eduardo/Documentos/nexo/venv/bin/activate
echo "✅ Ambiente ativado"

echo "⬇️ Instalando dependências..."
pip install -r requirements.txt --quiet
echo "✅ Dependências instaladas"

echo "🗃️ Executando migrações..."
python manage.py migrate --noinput
echo "✅ Migrações executadas"

echo "🧹 Limpando cache e arquivos estáticos antigos..."
# Limpar completamente os arquivos estáticos antigos
sudo rm -rf /var/www/nexo_static/*
python manage.py collectstatic --noinput --clear
echo "✅ Cache limpo e arquivos coletados"

echo "🌐 Sincronizando arquivos para nginx (FORÇADO)..."
# Forçar sincronização para nginx
sudo rsync -av --delete --force ./staticfiles/ /var/www/nexo_static/
echo "✅ Arquivos sincronizados para nginx"

echo "🔄 Forçando limpeza total do cache do nginx..."
# Parar nginx para forçar limpeza do cache
sudo systemctl stop nginx
sleep 2
# Limpar qualquer cache persistente do nginx
sudo rm -rf /var/cache/nginx/*
# Reiniciar nginx
sudo systemctl start nginx
sudo systemctl reload nginx
echo "✅ Cache do nginx limpo completamente"

echo "🚀 Reiniciando Gunicorn..."
sudo systemctl restart gunicorn_nexo
sleep 3
echo "✅ Gunicorn reiniciado"

echo ""
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "================================"
echo "🌐 Produção: https://10.209.15.176/"
echo "📋 Simulador: https://10.209.15.176/simulador/"
echo ""

# Verificar se tudo está funcionando
echo "🔍 Verificando status dos serviços..."
if sudo systemctl is-active --quiet nginx && sudo systemctl is-active --quiet gunicorn_nexo; then
    echo "✅ Todos os serviços estão ativos"
    echo "🎯 Deploy aplicado com sucesso!"
else
    echo "❌ Erro: Alguns serviços não estão funcionando"
    echo "📋 Status Nginx: $(sudo systemctl is-active nginx)"
    echo "📋 Status Gunicorn: $(sudo systemctl is-active gunicorn_nexo)"
fi 