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

# Obter credenciais do Google OAuth de variáveis de ambiente
client_id = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")

# Configure o aplicativo social do Google
google_app, created = SocialApp.objects.get_or_create(
    provider="google",
    defaults={
        "name": "Google OAuth",
        "client_id": client_id,
        "secret": client_secret,
        "key": "",
    },
)

if not created:
    google_app.client_id = client_id
    google_app.secret = client_secret
    google_app.save()

# Associe o aplicativo ao site
google_app.sites.add(site)

print("Site configurado:", site)
print("Aplicativo social Google configurado:", google_app)
