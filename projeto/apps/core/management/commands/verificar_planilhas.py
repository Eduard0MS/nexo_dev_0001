import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import PlanilhaImportada


class Command(BaseCommand):
    help = 'Verifica e corrige registros de planilhas que apontam para arquivos inexistentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corrige automaticamente os problemas encontrados',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando planilhas importadas...")
        
        planilhas = PlanilhaImportada.objects.all()
        problems_found = []
        existing_files = []
        
        # Check each planilha record
        for planilha in planilhas:
            file_path = planilha.arquivo.path
            
            if os.path.exists(file_path):
                existing_files.append(planilha)
                status = "✅ EXISTE"
            else:
                problems_found.append(planilha)
                status = "❌ NÃO ENCONTRADO"
            
            active_status = "🟢 ATIVO" if planilha.ativo else "⚪ INATIVO"
            
            self.stdout.write(
                f"  [{active_status}] {planilha.nome} - {status}"
            )
            self.stdout.write(f"      📂 {file_path}")
        
        # Report summary
        self.stdout.write("\n📊 RESUMO:")
        self.stdout.write(f"  Total de planilhas: {planilhas.count()}")
        self.stdout.write(f"  Arquivos existentes: {len(existing_files)}")
        self.stdout.write(f"  Problemas encontrados: {len(problems_found)}")
        
        # Check if there's an active planilha
        active_planilhas = planilhas.filter(ativo=True)
        if active_planilhas.count() == 0:
            self.stdout.write("\n⚠️  AVISO: Nenhuma planilha ativa encontrada!")
        elif active_planilhas.count() > 1:
            self.stdout.write(f"\n⚠️  AVISO: {active_planilhas.count()} planilhas ativas encontradas (deveria ser apenas 1)")
        else:
            active_planilha = active_planilhas.first()
            if not os.path.exists(active_planilha.arquivo.path):
                self.stdout.write("\n❌ ERRO: A planilha ativa aponta para um arquivo inexistente!")
            else:
                self.stdout.write(f"\n✅ OK: Planilha ativa '{active_planilha.nome}' está funcionando")
        
        # Apply fixes if requested
        if options['fix']:
            self.stdout.write("\n🔧 APLICANDO CORREÇÕES...")
            
            # Remove records pointing to non-existent files
            if problems_found:
                self.stdout.write(f"  Removendo {len(problems_found)} registros órfãos...")
                for planilha in problems_found:
                    self.stdout.write(f"    🗑️  Removendo: {planilha.nome}")
                    planilha.delete()
            
            # Ensure we have exactly one active planilha
            remaining_planilhas = PlanilhaImportada.objects.all()
            active_count = remaining_planilhas.filter(ativo=True).count()
            
            if active_count == 0 and remaining_planilhas.exists():
                # Set the most recent one as active
                latest_planilha = remaining_planilhas.order_by('-data_importacao').first()
                latest_planilha.ativo = True
                latest_planilha.save()
                self.stdout.write(f"  ✅ Definindo '{latest_planilha.nome}' como planilha ativa")
            
            elif active_count > 1:
                # Keep only the most recent one as active
                active_planilhas = remaining_planilhas.filter(ativo=True).order_by('-data_importacao')
                keep_active = active_planilhas.first()
                
                for planilha in active_planilhas[1:]:
                    planilha.ativo = False
                    planilha.save()
                    self.stdout.write(f"  🔄 Desativando: {planilha.nome}")
                
                self.stdout.write(f"  ✅ Mantendo '{keep_active.nome}' como única planilha ativa")
            
            self.stdout.write("\n✅ Correções aplicadas com sucesso!")
        else:
            if problems_found or active_planilhas.count() != 1:
                self.stdout.write("\n💡 Para corrigir os problemas automaticamente, execute:")
                self.stdout.write("   python manage.py verificar_planilhas --fix") 