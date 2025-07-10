import os
import django
import sqlite3
import dotenv

# Carregar variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from django.conf import settings
from django.db import connection
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Inspecionar aplicativos sociais com ORM
print("=== DETALHES DOS APLICATIVOS SOCIAIS VIA ORM ===")
all_apps = SocialApp.objects.all()
print(f"Total de aplicativos sociais: {all_apps.count()}")

for i, app in enumerate(all_apps):
    print(f"\nAplicativo #{i+1}")
    print(f"  ID: {app.id}")
    print(f"  Nome: {app.name}")
    print(f"  Provider: {app.provider}")
    print(f"  Client ID: {app.client_id}")
    print(f"  Secret: {app.secret[:5]}..." if app.secret else "  Secret: Vazio")
    print(f"  Key: {app.key}")
    print(f"  Sites associados: {[s.domain for s in app.sites.all()]}")

# Conectar diretamente ao SQLite para uma inspeção mais profunda
db_path = settings.DATABASES["default"]["NAME"]
print(f"\n=== ACESSANDO BANCO DE DADOS DIRETAMENTE: {db_path} ===")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver todas as tabelas relacionadas a socialaccount
print("\nTabelas relacionadas a socialaccount:")
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%social%'"
)
tables = cursor.fetchall()
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  {table_name}: {count} registros")

# Examinar a tabela socialaccount_socialapp diretamente
print("\nExaminando socialaccount_socialapp diretamente:")
cursor.execute("SELECT id, provider, name, client_id FROM socialaccount_socialapp")
rows = cursor.fetchall()
print(f"Total de registros: {len(rows)}")
for row in rows:
    print(
        f"  ID: {row[0]}, Provider: '{row[1]}', Nome: '{row[2]}', Client ID: {row[3][:20]}..."
    )

# Verificar aplicativos Google
print("\nAplicativos Google:")
cursor.execute(
    "SELECT id, provider, name, client_id FROM socialaccount_socialapp WHERE provider='google' OR provider LIKE '%google%'"
)
google_apps = cursor.fetchall()
print(f"Total: {len(google_apps)}")
for app in google_apps:
    print(f"  ID: {app[0]}, Provider: '{app[1]}', Nome: '{app[2]}'")

# Verificar associações
print("\nAssociações app-site:")
cursor.execute(
    """
SELECT sa.id, sa.provider, sa.name, ds.domain 
FROM socialaccount_socialapp sa
JOIN socialaccount_socialapp_sites sas ON sa.id = sas.socialapp_id
JOIN django_site ds ON ds.id = sas.site_id
"""
)
associations = cursor.fetchall()
print(f"Total: {len(associations)}")
for assoc in associations:
    print(f"  App ID: {assoc[0]}, Provider: '{assoc[1]}', Site: {assoc[3]}")

# Procurar por registros órfãos ou inválidos
print("\nVerificando registros com provider NULL ou vazio:")
cursor.execute(
    "SELECT id, provider, name FROM socialaccount_socialapp WHERE provider IS NULL OR provider = ''"
)
invalid_provider = cursor.fetchall()
if invalid_provider:
    print(f"  Encontrados {len(invalid_provider)} registros:")
    for app in invalid_provider:
        print(f"  ID: {app[0]}, Provider: '{app[1]}', Nome: '{app[2]}'")
else:
    print("  Nenhum registro com provider NULL ou vazio encontrado.")

# CORREÇÃO: Excluir registros inválidos
print("\n=== LIMPEZA RADICAL ===")
try:
    # Iniciar transação para garantir atomicidade
    conn.execute("BEGIN TRANSACTION")

    # 1. Excluir associações app-site
    cursor.execute("DELETE FROM socialaccount_socialapp_sites")
    print(f"Associações excluídas: {cursor.rowcount}")

    # 2. Excluir todos os aplicativos sociais
    cursor.execute("DELETE FROM socialaccount_socialapp")
    print(f"Aplicativos excluídos: {cursor.rowcount}")

    # 3. Recriar o site
    cursor.execute(
        "UPDATE django_site SET domain='127.0.0.1:8000', name='Nexo Local' WHERE id=1"
    )
    print(f"Site atualizado: {cursor.rowcount}")

    # 4. Criar um novo aplicativo Google
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")

    cursor.execute(
        """
    INSERT INTO socialaccount_socialapp (provider, name, client_id, secret, key)
    VALUES ('google', 'Google OAuth', ?, ?, '')
    """,
        (client_id, client_secret),
    )
    new_app_id = cursor.lastrowid
    print(f"Novo aplicativo criado com ID: {new_app_id}")

    # 5. Associar ao site
    cursor.execute(
        """
    INSERT INTO socialaccount_socialapp_sites (socialapp_id, site_id)
    VALUES (?, 1)
    """,
        (new_app_id,),
    )
    print(f"Associação criada")

    # Confirmar alterações
    conn.commit()
    print("Transação concluída com sucesso!")

except Exception as e:
    conn.rollback()
    print(f"ERRO: {e}")
    print("Transação revertida")

finally:
    # Verificar resultado final
    cursor.execute("SELECT id, provider, name FROM socialaccount_socialapp")
    final_apps = cursor.fetchall()
    print(f"\nAplicativos finais: {len(final_apps)}")
    for app in final_apps:
        print(f"  ID: {app[0]}, Provider: '{app[1]}', Nome: '{app[2]}'")

    conn.close()

print("\nReinicie o servidor Django para aplicar as alterações!")
