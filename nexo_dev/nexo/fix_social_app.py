import os
import django
import time
import dotenv

# Carregar variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import connection

# Verificar aplicativos existentes para o Google
existing_apps = SocialApp.objects.filter(provider="google")
print(f"Aplicativos Google existentes antes da limpeza: {existing_apps.count()}")
for app in existing_apps:
    print(f"ID: {app.id}, Nome: {app.name}, Client ID: {app.client_id[:10]}...")
    # Remover as associações de sites primeiro
    app.sites.clear()
    # Excluir o aplicativo
    app.delete()
    print(f"Aplicativo ID {app.id} excluído")

# Executar SQL direto para garantir a limpeza
cursor = connection.cursor()
cursor.execute("DELETE FROM socialaccount_socialapp WHERE provider = 'google'")
print(f"SQL direto executado, {cursor.rowcount} linhas afetadas")

# Verificar novamente
time.sleep(1)  # Pequena pausa para garantir que a transação foi concluída
print(
    f"Aplicativos Google após limpeza: {SocialApp.objects.filter(provider='google').count()}"
)

# Atualizar o site para apontar para o endereço local correto
site = Site.objects.get(id=1)
old_domain = site.domain
site.domain = "127.0.0.1:8000"  # Usando 127.0.0.1 em vez de localhost
site.name = "Nexo Local Development"
site.save()
print(f"Site atualizado: {old_domain} -> {site.domain}")

# Criar novo aplicativo social do Google
google_app = SocialApp.objects.create(
    provider="google",
    name="Google OAuth",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE"),
    secret=os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE"),
    key="",
)

# Associar o aplicativo ao site
google_app.sites.add(site)

print(f"Novo aplicativo social Google configurado: {google_app}")
print(f"ID: {google_app.id}, Provider: {google_app.provider}")
print(f"Sites associados: {[s.domain for s in google_app.sites.all()]}")
print(
    f"Número final de aplicativos Google no banco de dados: {SocialApp.objects.filter(provider='google').count()}"
)
