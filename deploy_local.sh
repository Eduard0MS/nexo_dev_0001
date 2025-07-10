#!/bin/bash
# 🚀 Deploy Local Automático - Nexo

echo "🚀 DEPLOY LOCAL INICIADO"
echo "========================"

# Navegar para diretório do projeto
cd /home/eduardo/Documentos/nexo/nexo_dev_0001

echo "🔄 Atualizando código do GitHub..."
git fetch origin
git reset --hard origin/main
echo "✅ Código atualizado"

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

echo "📋 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
echo "✅ Static files coletados"

echo "🔄 Reiniciando Gunicorn..."
sudo systemctl restart gunicorn_nexo
echo "✅ Gunicorn reiniciado"

sleep 3

echo "✅ Verificando status..."
if sudo systemctl is-active gunicorn_nexo > /dev/null; then
    echo "✅ Gunicorn está ativo"
    echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
else
    echo "❌ Erro: Gunicorn não está ativo"
    sudo systemctl status gunicorn_nexo
    exit 1
fi 