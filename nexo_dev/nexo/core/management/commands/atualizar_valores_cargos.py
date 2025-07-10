from django.core.management.base import BaseCommand
from core.models import UnidadeCargo, CargoSIORG
from decimal import Decimal


class Command(BaseCommand):
    help = "Atualiza os valores de pontos_total e valor_total na tabela UnidadeCargo com base nos dados do CargoSIORG"

    def handle(self, *args, **options):
        # Buscar todos os cargos SIORG para referência
        cargos_siorg = {
            f"{cargo.cargo}": {
                "valor": Decimal(
                    cargo.valor.replace("R$ ", "").replace(".", "").replace(",", ".")
                ),
                "unitario": cargo.unitario,
            }
            for cargo in CargoSIORG.objects.all()
        }

        # Buscar todas as unidades de cargo
        unidades = UnidadeCargo.objects.all()
        total_unidades = unidades.count()
        atualizadas = 0

        self.stdout.write(f"Total de unidades a processar: {total_unidades}")

        for unidade in unidades:
            # Formar a chave do cargo para busca
            cargo_key = f"{unidade.tipo_cargo} {unidade.categoria} {unidade.nivel:02d}"

            # Buscar informações do cargo no dicionário
            cargo_info = cargos_siorg.get(
                cargo_key, {"valor": Decimal("0"), "unitario": Decimal("0")}
            )

            # Calcular valores totais
            valor_total = cargo_info["valor"] * unidade.quantidade
            pontos_total = cargo_info["unitario"] * unidade.quantidade

            # Atualizar a unidade
            unidade.valor_total = valor_total
            unidade.pontos_total = pontos_total
            unidade.save()

            atualizadas += 1
            if atualizadas % 100 == 0:
                self.stdout.write(
                    f"Processadas {atualizadas}/{total_unidades} unidades"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Processo concluído! {atualizadas} unidades atualizadas."
            )
        )
