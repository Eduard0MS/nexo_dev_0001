from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.core.models import UnidadeCargo

class Command(BaseCommand):
    help = 'Remove registros inválidos (sem grafo e categoria "Colegiado") da tabela UnidadeCargo'

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
        registros_sem_grafo = UnidadeCargo.objects.filter(
            Q(grafo__exact='') | Q(grafo__isnull=True)
        )
        qtd_sem_grafo = registros_sem_grafo.count()
        
        # Identificar registros com categoria 'Colegiado'
        registros_colegiado = UnidadeCargo.objects.filter(categoria_unidade__icontains='Colegiado')
        qtd_colegiado = registros_colegiado.count()
        
        total_invalidos = qtd_sem_grafo + qtd_colegiado
        
        # Exibir informações
        self.stdout.write(f"Registros sem grafo encontrados: {qtd_sem_grafo}")
        self.stdout.write(f"Registros com categoria 'Colegiado' encontrados: {qtd_colegiado}")
        self.stdout.write(f"Total de registros inválidos: {total_invalidos}")
        
        if total_invalidos == 0:
            self.stdout.write(self.style.SUCCESS("Não há registros inválidos para remover."))
            return
        
        # Se não for apenas simulação, remover os registros
        if not dry_run:
            registros_sem_grafo.delete()
            registros_colegiado.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Removidos {total_invalidos} registros inválidos ({qtd_sem_grafo} sem grafo + {qtd_colegiado} categoria 'Colegiado'). "
                    f"Agora restam {total_registros - total_invalidos} registros válidos."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Modo simulação: {total_invalidos} registros seriam removidos ({qtd_sem_grafo} sem grafo + {qtd_colegiado} categoria 'Colegiado'). "
                    f"Execute sem --dry-run para remover de fato."
                )
            ) 