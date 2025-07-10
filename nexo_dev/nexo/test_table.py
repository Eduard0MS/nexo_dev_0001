import os
import sys
import django
from django.conf import settings

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from django.utils import timezone
from core.models import CargoSIORG


def test_table():
    try:
        # Tentar criar um registro de teste
        cargo = CargoSIORG.objects.create(
            cargo="TESTE FCE", nivel="N1", quantidade=1, valor="R$ 1.000,00"
        )
        print("Registro de teste criado com sucesso!")

        # Tentar recuperar o registro
        cargo_recuperado = CargoSIORG.objects.get(id=cargo.id)
        print(f"Cargo recuperado: {cargo_recuperado.cargo}")

        # Limpar o registro de teste
        cargo.delete()
        print("Registro de teste removido com sucesso!")

        print("\nTabela está funcionando corretamente!")

    except Exception as e:
        print(f"Erro ao testar a tabela: {str(e)}")


if __name__ == "__main__":
    test_table()
