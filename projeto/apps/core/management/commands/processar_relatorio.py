"""
Comando de gerenciamento para processar relatórios.
Uso: python manage.py processar_relatorio --arquivo /caminho/para/arquivo.xlsx --tipo gratificacoes --nome "Nome do Relatório"
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.models import Relatorio
from core.relatorio_processor import processar_relatorio, obter_estatisticas_relatorio
import os


class Command(BaseCommand):
    help = 'Processa um relatório Excel e salva os dados no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            type=str,
            required=True,
            help='Caminho para o arquivo Excel a ser processado'
        )
        parser.add_argument(
            '--tipo',
            type=str,
            required=True,
            choices=['gratificacoes', 'orgaos', 'efetivo', 'facilities', 'outro'],
            help='Tipo do relatório a ser processado'
        )
        parser.add_argument(
            '--nome',
            type=str,
            required=True,
            help='Nome para identificar o relatório'
        )
        parser.add_argument(
            '--descricao',
            type=str,
            default='',
            help='Descrição opcional do relatório'
        )
        parser.add_argument(
            '--usuario',
            type=str,
            default='admin',
            help='Username do usuário responsável pelo upload (padrão: admin)'
        )

    def handle(self, *args, **options):
        arquivo_path = options['arquivo']
        tipo = options['tipo']
        nome = options['nome']
        descricao = options['descricao']
        username = options['usuario']

        # Verificar se o arquivo existe
        if not os.path.exists(arquivo_path):
            raise CommandError(f'Arquivo não encontrado: {arquivo_path}')

        # Verificar se é um arquivo Excel
        if not arquivo_path.lower().endswith(('.xlsx', '.xls')):
            raise CommandError('O arquivo deve ser uma planilha Excel (.xlsx ou .xls)')

        # Obter o usuário
        try:
            usuario = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'Usuário "{username}" não encontrado. Criando relatório sem usuário associado.')
            )
            usuario = None

        # Criar o objeto Relatorio
        try:
            relatorio = Relatorio.objects.create(
                nome=nome,
                tipo=tipo,
                descricao=descricao,
                usuario_upload=usuario,
                arquivo=arquivo_path
            )
            
            self.stdout.write(f'Relatório criado: {relatorio.nome} (ID: {relatorio.id})')
            
        except Exception as e:
            raise CommandError(f'Erro ao criar relatório: {str(e)}')

        # Processar o relatório
        self.stdout.write('Iniciando processamento...')
        
        try:
            sucesso, mensagem = processar_relatorio(relatorio)
            
            if sucesso:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Processamento concluído: {mensagem}')
                )
                
                # Mostrar estatísticas
                stats = obter_estatisticas_relatorio(relatorio)
                if stats:
                    self.stdout.write('\n📊 Estatísticas do relatório processado:')
                    for chave, valor in stats.items():
                        self.stdout.write(f'  • {chave.replace("_", " ").title()}: {valor}')
                        
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro no processamento: {mensagem}')
                )
                
        except Exception as e:
            raise CommandError(f'Erro durante o processamento: {str(e)}')

        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Relatório processado com ID: {relatorio.id}')
        self.stdout.write(f'Acesse o admin em: /admin/core/relatorio/{relatorio.id}/change/')
        
        if relatorio.processado:
            self.stdout.write(f'Estatísticas em: /admin/core/relatorio/{relatorio.id}/estatisticas/') 