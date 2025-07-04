import os
import django
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

# Encontrar o caminho para o django-allauth
import allauth

allauth_path = Path(allauth.__file__).parent
adapter_path = allauth_path / "socialaccount" / "adapter.py"

print(f"Caminho do adapter.py: {adapter_path}")

if not adapter_path.exists():
    print("Arquivo adapter.py não encontrado!")
    exit(1)

# Ler o conteúdo original
with open(adapter_path, "r", encoding="utf-8") as f:
    original_content = f.read()

# Fazer backup do arquivo original
backup_path = adapter_path.with_suffix(".py.bak")
with open(backup_path, "w", encoding="utf-8") as f:
    f.write(original_content)
print(f"Backup criado em: {backup_path}")

# Encontrar a função get_app e modificá-la
pattern = r"def get_app\(self, request=None, provider=None, client_id=None\):(.*?)return visible_apps\[0\]"
replacement = """def get_app(self, request=None, provider=None, client_id=None):
        SocialApp = apps.get_model("socialaccount", "SocialApp")
        
        # Trata o caso especial de provider='google'
        if provider == 'google':
            # Forçar sempre pegar o primeiro aplicativo Google com client_id não vazio
            app = SocialApp.objects.filter(provider=provider).filter(client_id__isnull=False).filter(client_id__gt='').first()
            if app:
                return app
                
        # Implementação original
        qs = SocialApp.objects.all()
        if provider:
            qs = qs.filter(provider=provider)
        if client_id:
            qs = qs.filter(client_id=client_id)
        apps = qs.filter(sites__id=get_current_site(request).id).distinct()
        visible_apps = list(apps)
        if not visible_apps:
            apps = qs
            visible_apps = list(apps)
        if not visible_apps:
            raise SocialApp.DoesNotExist("No SocialApp found")
        if len(visible_apps) > 1:
            # Modificado para não lançar exceção
            # raise MultipleObjectsReturned
            # Em vez disso, retornar o primeiro
            return visible_apps[0]
        return visible_apps[0]"""

modified_content = re.sub(pattern, replacement, original_content, flags=re.DOTALL)

# Verificar se a modificação foi bem-sucedida
if modified_content == original_content:
    print("ERRO: Não foi possível aplicar o patch. Padrão não encontrado.")
    exit(1)

# Escrever o conteúdo modificado
with open(adapter_path, "w", encoding="utf-8") as f:
    f.write(modified_content)

print(
    "Patch aplicado com sucesso! Reinicie o servidor Django para que as alterações entrem em vigor."
)
print(
    "IMPORTANTE: Isso é uma solução temporária. Você deve resolver o problema raiz no banco de dados."
)
print(
    "Para reverter o patch, substitua o arquivo adapter.py pelo backup adaptador.py.bak"
)
