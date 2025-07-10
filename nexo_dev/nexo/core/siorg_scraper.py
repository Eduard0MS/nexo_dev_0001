import requests
from bs4 import BeautifulSoup
from .models import CargoSIORG
import logging
import re
from decimal import Decimal

logger = logging.getLogger(__name__)


def scrape_siorg():
    """
    Função para fazer scraping dos dados do SIORG e salvar no banco de dados.
    """
    try:
        # Limpa os dados existentes
        CargoSIORG.objects.all().delete()

        cargos_processados = 0

        # Processando CCE
        cce_rows = [
            # CCE 1
            ("CCE 1 18", "R$ 24.553,28", "7.65"),
            ("CCE 1 17", "R$ 22.718,03", "7.08"),
            ("CCE 1 16", "R$ 20.008,08", "6.23"),
            ("CCE 1 15", "R$ 17.373,92", "5.41"),
            ("CCE 1 14", "R$ 14.860,92", "4.63"),
            ("CCE 1 13", "R$ 13.229,07", "4.12"),
            ("CCE 1 12", "R$ 9.960,05", "3.10"),
            ("CCE 1 11", "R$ 7.941,89", "2.47"),
            ("CCE 1 10", "R$ 6.813,25", "2.12"),
            ("CCE 1 09", "R$ 5.349,34", "1.67"),
            ("CCE 1 08", "R$ 5.130,61", "1.60"),
            ("CCE 1 07", "R$ 4.447,45", "1.39"),
            ("CCE 1 06", "R$ 3.766,05", "1.17"),
            ("CCE 1 05", "R$ 3.209,60", "1.00"),
            ("CCE 1 04", "R$ 1.425,44", "0.44"),
            ("CCE 1 03", "R$ 1.187,56", "0.37"),
            ("CCE 1 02", "R$ 664,20", "0.21"),
            ("CCE 1 01", "R$ 393,01", "0.12"),
            # CCE 2
            ("CCE 2 17", "R$ 22.718,03", "7.08"),
            ("CCE 2 16", "R$ 20.008,08", "6.23"),
            ("CCE 2 15", "R$ 17.373,92", "5.41"),
            ("CCE 2 14", "R$ 14.860,92", "4.63"),
            ("CCE 2 13", "R$ 13.229,07", "4.12"),
            ("CCE 2 12", "R$ 9.960,05", "3.10"),
            ("CCE 2 11", "R$ 7.941,89", "2.47"),
            ("CCE 2 10", "R$ 6.813,25", "2.12"),
            ("CCE 2 09", "R$ 5.349,34", "1.67"),
            ("CCE 2 08", "R$ 5.130,61", "1.60"),
            ("CCE 2 07", "R$ 4.447,45", "1.39"),
            ("CCE 2 06", "R$ 3.766,05", "1.17"),
            ("CCE 2 05", "R$ 3.209,60", "1.00"),
            ("CCE 2 04", "R$ 1.425,44", "0.44"),
            ("CCE 2 03", "R$ 1.187,56", "0.37"),
            ("CCE 2 02", "R$ 664,20", "0.21"),
            ("CCE 2 01", "R$ 393,01", "0.12"),
            # CCE 3
            ("CCE 3 16", "R$ 20.008,08", "6.23"),
            ("CCE 3 15", "R$ 17.373,92", "5.41"),
            ("CCE 3 14", "R$ 14.860,92", "4.63"),
            ("CCE 3 13", "R$ 13.229,07", "4.12"),
            ("CCE 3 12", "R$ 9.960,05", "3.10"),
            ("CCE 3 11", "R$ 7.941,89", "2.47"),
            ("CCE 3 10", "R$ 6.813,25", "2.12"),
            ("CCE 3 09", "R$ 5.349,34", "1.67"),
            ("CCE 3 08", "R$ 5.130,61", "1.60"),
            ("CCE 3 07", "R$ 4.447,45", "1.39"),
            ("CCE 3 06", "R$ 3.766,05", "1.17"),
            ("CCE 3 05", "R$ 3.209,60", "1.00"),
            ("CCE 3 04", "R$ 1.425,44", "0.44"),
            ("CCE 3 03", "R$ 1.187,56", "0.37"),
            ("CCE 3 02", "R$ 664,20", "0.21"),
            ("CCE 3 01", "R$ 393,01", "0.12"),
        ]

        # Processando FCE
        fce_rows = [
            # FCE 1
            ("FCE 1 17", "R$ 13.630,81", "4.25"),
            ("FCE 1 16", "R$ 12.004,84", "3.74"),
            ("FCE 1 15", "R$ 10.424,34", "3.25"),
            ("FCE 1 14", "R$ 8.916,56", "2.78"),
            ("FCE 1 13", "R$ 7.937,44", "2.47"),
            ("FCE 1 12", "R$ 5.976,02", "1.86"),
            ("FCE 1 11", "R$ 4.765,13", "1.48"),
            ("FCE 1 10", "R$ 4.087,96", "1.27"),
            ("FCE 1 09", "R$ 3.209,60", "1.00"),
            ("FCE 1 08", "R$ 3.078,91", "0.96"),
            ("FCE 1 07", "R$ 2.668,47", "0.83"),
            ("FCE 1 06", "R$ 2.259,64", "0.70"),
            ("FCE 1 05", "R$ 1.925,77", "0.60"),
            ("FCE 1 04", "R$ 1.425,44", "0.44"),
            ("FCE 1 03", "R$ 1.187,56", "0.37"),
            ("FCE 1 02", "R$ 664,20", "0.21"),
            ("FCE 1 01", "R$ 393,01", "0.12"),
            # FCE 2
            ("FCE 2 17", "R$ 13.630,81", "4.25"),
            ("FCE 2 16", "R$ 12.004,84", "3.74"),
            ("FCE 2 15", "R$ 10.424,34", "3.25"),
            ("FCE 2 14", "R$ 8.916,56", "2.78"),
            ("FCE 2 13", "R$ 7.937,44", "2.47"),
            ("FCE 2 12", "R$ 5.976,02", "1.86"),
            ("FCE 2 11", "R$ 4.765,13", "1.48"),
            ("FCE 2 10", "R$ 4.087,96", "1.27"),
            ("FCE 2 09", "R$ 3.209,60", "1.00"),
            ("FCE 2 08", "R$ 3.078,91", "0.96"),
            ("FCE 2 07", "R$ 2.668,47", "0.83"),
            ("FCE 2 06", "R$ 2.259,64", "0.70"),
            ("FCE 2 05", "R$ 1.925,77", "0.60"),
            ("FCE 2 04", "R$ 1.425,44", "0.44"),
            ("FCE 2 03", "R$ 1.187,56", "0.37"),
            ("FCE 2 02", "R$ 664,20", "0.21"),
            ("FCE 2 01", "R$ 393,01", "0.12"),
            # FCE 3
            ("FCE 3 16", "R$ 12.004,84", "3.74"),
            ("FCE 3 15", "R$ 10.424,34", "3.25"),
            ("FCE 3 14", "R$ 8.916,56", "2.78"),
            ("FCE 3 13", "R$ 7.937,44", "2.47"),
            ("FCE 3 12", "R$ 5.976,02", "1.86"),
            ("FCE 3 11", "R$ 4.765,13", "1.48"),
            ("FCE 3 10", "R$ 4.087,96", "1.27"),
            ("FCE 3 09", "R$ 3.209,60", "1.00"),
            ("FCE 3 08", "R$ 3.078,91", "0.96"),
            ("FCE 3 07", "R$ 2.668,47", "0.83"),
            ("FCE 3 06", "R$ 2.259,64", "0.70"),
            ("FCE 3 05", "R$ 1.925,77", "0.60"),
            ("FCE 3 04", "R$ 1.425,44", "0.44"),
            ("FCE 3 03", "R$ 1.187,56", "0.37"),
            ("FCE 3 02", "R$ 664,20", "0.21"),
            ("FCE 3 01", "R$ 393,01", "0.12"),
            # FCE 4
            ("FCE 4 13", "R$ 7.937,44", "2.47"),
            ("FCE 4 12", "R$ 5.976,02", "1.86"),
            ("FCE 4 11", "R$ 4.765,13", "1.48"),
            ("FCE 4 10", "R$ 4.087,96", "1.27"),
            ("FCE 4 09", "R$ 3.209,60", "1.00"),
            ("FCE 4 08", "R$ 3.078,91", "0.96"),
            ("FCE 4 07", "R$ 2.668,47", "0.83"),
            ("FCE 4 06", "R$ 2.259,64", "0.70"),
            ("FCE 4 05", "R$ 1.925,77", "0.60"),
            ("FCE 4 04", "R$ 1.425,44", "0.44"),
            ("FCE 4 03", "R$ 1.187,56", "0.37"),
            ("FCE 4 02", "R$ 664,20", "0.21"),
            ("FCE 4 01", "R$ 393,01", "0.12"),
        ]

        # Processando CCE
        for cargo, valor, unitario in cce_rows:
            try:
                CargoSIORG.objects.create(
                    cargo=cargo,
                    nivel=unitario,  # O nível agora é o valor unitário
                    quantidade=1,  # Quantidade padrão, pode ser atualizada depois
                    valor=valor,
                    unitario=Decimal(unitario),  # Convertendo para Decimal
                )
                cargos_processados += 1
            except Exception as e:
                logger.error(f"Erro ao processar cargo {cargo}: {str(e)}")

        # Processando FCE
        for cargo, valor, unitario in fce_rows:
            try:
                CargoSIORG.objects.create(
                    cargo=cargo,
                    nivel=unitario,  # O nível agora é o valor unitário
                    quantidade=1,  # Quantidade padrão, pode ser atualizada depois
                    valor=valor,
                    unitario=Decimal(unitario),  # Convertendo para Decimal
                )
                cargos_processados += 1
            except Exception as e:
                logger.error(f"Erro ao processar cargo {cargo}: {str(e)}")

        if cargos_processados == 0:
            return {"success": False, "message": "Nenhum cargo processado."}

        return {
            "success": True,
            "message": f"Processados {cargos_processados} cargos com sucesso",
        }

    except Exception as e:
        logger.error(f"Erro ao processar os dados: {str(e)}")
        return {"success": False, "message": f"Erro ao processar os dados: {str(e)}"}
