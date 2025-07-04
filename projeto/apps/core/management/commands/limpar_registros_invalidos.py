from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import UnidadeCargo

class Command(BaseCommand):
    help = 'Remove registros inválidos (sem grafo) da tabela UnidadeCargo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quantos registros seriam removidos, sem executar a remoção'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Contar registros totais
        total_registros = UnidadeCargo.objects.count()
        self.stdout.write(f"Total de registros: {total_registros}")
        
        # Identificar registros inválidos (sem grafo ou com grafo vazio)
        registros_invalidos = UnidadeCargo.objects.filter(
            Q(grafo__exact='') | Q(grafo__isnull=True)
        )
        qtd_invalidos = registros_invalidos.count()
        
        # Exibir informações
        self.stdout.write(f"Registros inválidos encontrados: {qtd_invalidos}")
        
        if qtd_invalidos == 0:
            self.stdout.write(self.style.SUCCESS("Não há registros inválidos para remover."))
            return
        
        # Se não for apenas simulação, remover os registros
        if not dry_run:
            registros_invalidos.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Removidos {qtd_invalidos} registros inválidos. "
                    f"Agora restam {total_registros - qtd_invalidos} registros válidos."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Modo simulação: {qtd_invalidos} registros seriam removidos. "
                    f"Execute sem --dry-run para remover de fato."
                )
            ) 