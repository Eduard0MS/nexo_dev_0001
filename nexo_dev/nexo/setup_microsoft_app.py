import os
import django
import dotenv

# Carregar variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Certifique-se de que o site com ID 1 exista e aponte para o localhost
site, created = Site.objects.get_or_create(
    id=1, defaults={"domain": "localhost:8000", "name": "Nexo Local Development"}
)

if not created:
    site.domain = "localhost:8000"
    site.name = "Nexo Local Development"
    site.save()

# Obter credenciais do Microsoft OAuth de variáveis de ambiente
client_id = os.environ.get("MICROSOFT_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")

# Configure o aplicativo social do Microsoft
microsoft_app, created = SocialApp.objects.get_or_create(
    provider="microsoft",
    defaults={
        "name": "Microsoft OAuth",
        "client_id": client_id,
        "secret": client_secret,
        "key": "",
    },
)

if not created:
    microsoft_app.client_id = client_id
    microsoft_app.secret = client_secret
    microsoft_app.save()

# Associe o aplicativo ao site
microsoft_app.sites.add(site)

print("Site configurado:", site)
print("Aplicativo social Microsoft configurado:", microsoft_app)
