import os
import django
import mysql.connector
from django.conf import settings

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

# Configurações do MySQL
mysql_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "1802Edu0#*#",
    "database": "nexo_dev",
}

try:
    # Conectar ao MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    print("Conexão com MySQL estabelecida com sucesso!")

    # Listar todas as tabelas
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    print("\nTabelas no banco de dados:")
    for table in tables:
        print(f"- {table[0]}")

        # Mostrar número de registros em cada tabela
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Registros: {count}")

    conn.close()
    print("\nVerificação concluída com sucesso!")

except Exception as e:
    print(f"Erro ao conectar ao MySQL: {str(e)}")
