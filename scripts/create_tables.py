import os
import django
from django.db import connection

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

# SQL para criar a tabela CargoSIORG
sql = """
CREATE TABLE IF NOT EXISTS core_cargosiorg (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cargo VARCHAR(255) NOT NULL,
    nivel VARCHAR(50) NOT NULL,
    quantidade INTEGER NOT NULL,
    valor VARCHAR(50) NOT NULL,
    data_atualizacao DATETIME NOT NULL
);
"""

try:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        print("Tabela CargoSIORG criada com sucesso!")
except Exception as e:
    print(f"Erro ao criar a tabela: {str(e)}") 