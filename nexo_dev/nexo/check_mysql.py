import os
import django
import mysql.connector
import re
from django.conf import settings

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()


# Função para validar nome de tabela de forma segura
def is_safe_table_name(table_name):
    """Valida se o nome da tabela contém apenas caracteres seguros."""
    # Permite apenas letras, números, underscore - padrão MySQL
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name))


# Configurações do MySQL
mysql_config = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "nexo_dev"),
}

try:
    # Conectar ao MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    print("Conexão com MySQL estabelecida com sucesso!")

    # Listar todas as tabelas
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    # Criar lista de nomes de tabelas válidas para segurança
    valid_table_names = [table[0] for table in tables]

    print("\nTabelas no banco de dados:")
    for table in tables:
        table_name = table[0]
        print(f"- {table_name}")

        # SEGURANÇA: Validação rigorosa do nome da tabela
        if (
            table_name in valid_table_names
            and is_safe_table_name(table_name)
            and len(table_name) <= 64
        ):  # Limite do MySQL para nomes de tabela
            # Usar placeholder %s para o nome da tabela não funciona, então usamos validação rigorosa
            # SEGURANÇA: SQL injection prevenida por validação regex + whitelist + limite de tamanho
            query = f"SELECT COUNT(*) FROM `{table_name}`"  # nosec B608
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  Registros: {count}")
        else:
            print(f"  Registros: ERRO - Nome de tabela inválido ou não seguro")

    conn.close()
    print("\nVerificação concluída com sucesso!")

except Exception as e:
    print(f"Erro ao conectar ao MySQL: {str(e)}")
