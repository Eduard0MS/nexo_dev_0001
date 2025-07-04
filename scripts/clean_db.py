import os
import django
import sqlite3
import dotenv

# Carregar variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from django.conf import settings
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Usar o Django ORM para limpar e recriar
print("Limpando e recriando com Django ORM...")

# 1. Remover associações e aplicativos existentes
SocialApp.objects.filter(provider__in=["google", "microsoft"]).delete()
print("Aplicativos sociais do Google e Microsoft removidos")

# 2. Atualizar o site
site = Site.objects.get(id=1)
site.domain = "127.0.0.1:8000"
site.name = "Nexo Local Development"
site.save()
print(f"Site atualizado: {site.domain}")

# 3. Criar novo aplicativo Google
google_app = SocialApp.objects.create(
    provider="google",
    name="Google OAuth",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE"),
    secret=os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE"),
    key="",
)
google_app.sites.add(site)
print(f"Novo aplicativo Google criado: {google_app.id}")

# 4. Criar novo aplicativo Microsoft
microsoft_app = SocialApp.objects.create(
    provider="microsoft",
    name="Microsoft OAuth",
    client_id=os.environ.get("MICROSOFT_CLIENT_ID", "YOUR_CLIENT_ID_HERE"),
    secret=os.environ.get("MICROSOFT_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE"),
    key="",
)
microsoft_app.sites.add(site)
print(f"Novo aplicativo Microsoft criado: {microsoft_app.id}")

# 5. Verificar resultado
print("\nConfigurações atuais:")
for app in SocialApp.objects.all():
    print(
        f"Aplicativo: {app.id}, Provider: {app.provider}, Sites: {[s.domain for s in app.sites.all()]}"
    )

print("\nLimpeza e recriação concluídas com sucesso.")
