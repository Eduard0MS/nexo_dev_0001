"""
Comando para gerar documentação do sistema Nexo usando Sphinx.

Este comando oferece funcionalidades CRUD para a documentação:
- CREATE: Gerar nova documentação
- READ: Visualizar documentação existente  
- UPDATE: Atualizar documentação existente
- DELETE: Limpar arquivos de documentação

Uso:
    python manage.py gerar_documentacao --acao create
    python manage.py gerar_documentacao --acao update
    python manage.py gerar_documentacao --acao read --servidor
    python manage.py gerar_documentacao --acao delete
"""
import sphinx
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.template.loader import render_to_string
from django.apps import apps
from django.db import models
from core.models import *


class Command(BaseCommand):
    help = 'Sistema CRUD para documentação do projeto usando Sphinx'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--acao',
            type=str,
            choices=['create', 'read', 'update', 'delete', 'auto'],
            default='auto',
            help='Ação a ser executada: create, read, update, delete ou auto'
        )
        
        parser.add_argument(
            '--formato',
            type=str,
            choices=['html', 'pdf', 'epub', 'latex'],
            default='html',
            help='Formato de saída da documentação'
        )
        
        parser.add_argument(
            '--servidor',
            action='store_true',
            help='Iniciar servidor de desenvolvimento da documentação'
        )
        
        parser.add_argument(
            '--port',
            type=int,
            default=8080,
            help='Porta para o servidor de documentação (padrão: 8080)'
        )
        
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Modo watch: recompila automaticamente quando arquivos mudam'
        )
        
        parser.add_argument(
            '--incluir-frontend',
            action='store_true',
            help='Incluir documentação do frontend (JS, CSS, templates)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Saída detalhada'
        )

    def handle(self, *args, **options):
        self.verbosity = 2 if options['verbose'] else 1
        self.docs_path = Path(settings.BASE_DIR) / 'docs'
        self.build_path = self.docs_path / '_build'
        
        try:
            # Verificar se Sphinx está instalado
            self._verificar_sphinx()
            
            acao = options['acao']
            
            if acao == 'create':
                self._create_documentacao(options)
            elif acao == 'read':
                self._read_documentacao(options)
            elif acao == 'update':
                self._update_documentacao(options)
            elif acao == 'delete':
                self._delete_documentacao(options)
            elif acao == 'auto':
                self._auto_documentacao(options)
                
        except Exception as e:
            raise CommandError(f'Erro ao executar comando: {str(e)}')

    def _verificar_sphinx(self):
        """Verifica se Sphinx está instalado e disponível."""
        try:
            import sphinx
            self.stdout.write(
                self.style.SUCCESS(f'✓ Sphinx {sphinx.__version__} encontrado')
            )
        except ImportError:
            raise CommandError(
                'Sphinx não encontrado. Instale com: pip install -r requirements-docs.txt'
            )

    def _create_documentacao(self, options):
        """CREATE: Gera nova documentação completa."""
        self.stdout.write(
            self.style.WARNING('📝 Criando nova documentação...')
        )
        
        # Criar estrutura de diretórios
        self._criar_estrutura_diretorios()
        
        # Gerar arquivos de documentação automática
        self._gerar_documentacao_automatica(options)
        
        # Compilar documentação
        self._compilar_documentacao(options['formato'])
        
        self.stdout.write(
            self.style.SUCCESS('✅ Documentação criada com sucesso!')
        )

    def _read_documentacao(self, options):
        """READ: Visualiza documentação existente."""
        if not self.build_path.exists():
            raise CommandError('Documentação não encontrada. Execute com --acao create primeiro.')
        
        if options['servidor']:
            self._abrir_documentacao(options['servidor'], options['port'])
        else:
            # Abrir documentação no browser padrão
            import webbrowser
            index_path = self.build_path / 'html' / 'index.html'
            if index_path.exists():
                webbrowser.open(f'file://{index_path.absolute()}')
                self.stdout.write(
                    self.style.SUCCESS('📖 Documentação aberta no navegador')
                )
            else:
                raise CommandError('Arquivo index.html não encontrado')

    def _update_documentacao(self, options):
        """UPDATE: Atualiza documentação existente."""
        self.stdout.write(
            self.style.WARNING('🔄 Atualizando documentação...')
        )
        
        if options['watch']:
            self._modo_watch(options)
        else:
            # Gerar documentação automática atualizada
            self._gerar_documentacao_automatica(options)
            
            # Recompilar
            self._compilar_documentacao(options['formato'])
            
            self.stdout.write(
                self.style.SUCCESS('✅ Documentação atualizada!')
            )

    def _delete_documentacao(self, options):
        """DELETE: Remove arquivos de documentação."""
        self.stdout.write(
            self.style.WARNING('🗑️  Removendo documentação...')
        )
        
        if self.build_path.exists():
            shutil.rmtree(self.build_path)
            self.stdout.write(
                self.style.SUCCESS('✅ Arquivos de build removidos')
            )
        
        # Opcionalmente remover arquivos gerados automaticamente
        arquivos_auto = [
            self.docs_path / 'api' / 'auto_models.rst',
            self.docs_path / 'api' / 'auto_views.rst',
            self.docs_path / 'frontend' / 'auto_templates.rst',
        ]
        
        for arquivo in arquivos_auto:
            if arquivo.exists():
                arquivo.unlink()
                self.stdout.write(f'✓ Removido: {arquivo.name}')

    def _auto_documentacao(self, options):
        """AUTO: Modo automático - detecta estado e age adequadamente."""
        if not self.docs_path.exists():
            self.stdout.write('📝 Primeira execução - criando documentação...')
            self._create_documentacao(options)
        elif not self.build_path.exists():
            self.stdout.write('🔄 Build não encontrado - recompilando...')
            self._compilar_documentacao(options['formato'])
        else:
            self.stdout.write('🔄 Atualizando documentação existente...')
            self._update_documentacao(options)

    def _criar_estrutura_diretorios(self):
        """Cria estrutura de diretórios para documentação."""
        diretorios = [
            self.docs_path,
            self.docs_path / '_static',
            self.docs_path / '_templates',
            self.docs_path / 'api',
            self.docs_path / 'user-guide',
            self.docs_path / 'admin-guide',
            self.docs_path / 'development',
            self.docs_path / 'frontend',
            self.docs_path / 'examples',
        ]
        
        for diretorio in diretorios:
            diretorio.mkdir(parents=True, exist_ok=True)
            if self.verbosity > 1:
                self.stdout.write(f'✓ Diretório criado: {diretorio.name}')

    def _gerar_documentacao_automatica(self, options):
        """Gera documentação automática a partir do código."""
        
        # Documentação dos modelos
        self._gerar_doc_modelos()
        
        # Documentação das views
        self._gerar_doc_views()
        
        # Documentação dos forms
        self._gerar_doc_forms()
        
        # Documentação de utilitários
        self._gerar_doc_utils()
        
        if options['incluir_frontend']:
            # Documentação do frontend
            self._gerar_doc_frontend()

    def _gerar_doc_modelos(self):
        """Gera documentação automática dos modelos Django."""
        modelos = []
        
        for model in apps.get_models():
            if model._meta.app_label == 'core':  # Apenas modelos do app core
                modelos.append({
                    'nome': model.__name__,
                    'modulo': model.__module__,
                    'docstring': model.__doc__ or '',
                    'campos': [field.name for field in model._meta.fields],
                    'verbose_name': getattr(model._meta, 'verbose_name', model.__name__),
                })
        
        conteudo = self._renderizar_template('auto_models.rst', {
            'modelos': modelos,
            'data_geracao': 'now'
        })
        
        arquivo_saida = self.docs_path / 'api' / 'auto_models.rst'
        arquivo_saida.write_text(conteudo, encoding='utf-8')
        
        if self.verbosity > 1:
            self.stdout.write(f'✓ Gerado: {arquivo_saida.name}')

    def _gerar_doc_views(self):
        """Gera documentação automática das views."""
        from core import views
        import inspect
        
        views_info = []
        for nome, obj in inspect.getmembers(views):
            if inspect.isfunction(obj) and not nome.startswith('_'):
                views_info.append({
                    'nome': nome,
                    'docstring': obj.__doc__ or '',
                    'assinatura': str(inspect.signature(obj)),
                })
        
        conteudo = self._renderizar_template('auto_views.rst', {
            'views': views_info,
            'data_geracao': 'now'
        })
        
        arquivo_saida = self.docs_path / 'api' / 'auto_views.rst'
        arquivo_saida.write_text(conteudo, encoding='utf-8')

    def _gerar_doc_forms(self):
        """Gera documentação dos formulários."""
        try:
            from core import forms
            import inspect
            
            forms_info = []
            for nome, obj in inspect.getmembers(forms):
                if inspect.isclass(obj) and nome.endswith('Form'):
                    forms_info.append({
                        'nome': nome,
                        'docstring': obj.__doc__ or '',
                        'campos': getattr(obj.base_fields, 'keys', lambda: [])(),
                    })
            
            conteudo = self._renderizar_template('auto_forms.rst', {
                'forms': forms_info,
            })
            
            arquivo_saida = self.docs_path / 'api' / 'auto_forms.rst'
            arquivo_saida.write_text(conteudo, encoding='utf-8')
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️  Módulo forms não encontrado')
            )

    def _gerar_doc_utils(self):
        """Gera documentação dos utilitários."""
        try:
            from core import utils
            import inspect
            
            funcoes = []
            for nome, obj in inspect.getmembers(utils):
                if inspect.isfunction(obj) and not nome.startswith('_'):
                    funcoes.append({
                        'nome': nome,
                        'docstring': obj.__doc__ or '',
                        'assinatura': str(inspect.signature(obj)),
                    })
            
            conteudo = self._renderizar_template('auto_utils.rst', {
                'funcoes': funcoes,
            })
            
            arquivo_saida = self.docs_path / 'api' / 'auto_utils.rst'
            arquivo_saida.write_text(conteudo, encoding='utf-8')
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️  Módulo utils não encontrado')
            )

    def _gerar_doc_frontend(self):
        """Gera documentação do frontend."""
        templates_path = Path(settings.BASE_DIR) / 'core' / 'templates'
        static_path = Path(settings.BASE_DIR) / 'core' / 'static'
        
        # Documentar templates
        templates = []
        if templates_path.exists():
            for template_file in templates_path.rglob('*.html'):
                templates.append({
                    'nome': template_file.name,
                    'caminho': str(template_file.relative_to(templates_path)),
                    'tamanho': template_file.stat().st_size,
                })
        
        # Documentar arquivos CSS
        css_files = []
        if static_path.exists():
            for css_file in static_path.rglob('*.css'):
                css_files.append({
                    'nome': css_file.name,
                    'caminho': str(css_file.relative_to(static_path)),
                    'tamanho': css_file.stat().st_size,
                })
        
        # Documentar arquivos JavaScript
        js_files = []
        if static_path.exists():
            for js_file in static_path.rglob('*.js'):
                js_files.append({
                    'nome': js_file.name,
                    'caminho': str(js_file.relative_to(static_path)),
                    'tamanho': js_file.stat().st_size,
                })
        
        conteudo = self._renderizar_template('auto_frontend.rst', {
            'templates': templates,
            'css_files': css_files,
            'js_files': js_files,
        })
        
        arquivo_saida = self.docs_path / 'frontend' / 'auto_frontend.rst'
        arquivo_saida.write_text(conteudo, encoding='utf-8')

    def _renderizar_template(self, template_name, context):
        """Renderiza template RST com contexto."""
        
        # Renderização manual para evitar problemas com filtros Django
        if template_name == 'auto_models.rst':
            content = "Modelos (Gerado Automaticamente)\n"
            content += "=================================\n\n"
            content += ".. note::\n   Esta documentação foi gerada automaticamente.\n\n"
            
            for modelo in context.get('modelos', []):
                nome = modelo['nome']
                content += f"{nome}\n"
                content += "-" * len(nome) + "\n\n"
                content += f".. autoclass:: {modelo['modulo']}.{nome}\n"
                content += "   :members:\n"
                content += "   :undoc-members:\n"
                content += "   :show-inheritance:\n\n"
                
                content += "**Campos:**\n\n"
                for campo in modelo['campos']:
                    content += f"* ``{campo}``\n"
                
                content += f"\n**Nome legível:** {modelo['verbose_name']}\n\n"
                
                if modelo['docstring']:
                    content += "**Descrição:**\n\n"
                    content += f"{modelo['docstring']}\n\n"
            
            return content
            
        elif template_name == 'auto_views.rst':
            content = "Views (Gerado Automaticamente)\n"
            content += "===============================\n\n"
            content += ".. note::\n   Esta documentação foi gerada automaticamente.\n\n"
            
            for view in context.get('views', []):
                nome = view['nome']
                content += f"{nome}\n"
                content += "-" * len(nome) + "\n\n"
                content += f".. autofunction:: core.views.{nome}\n\n"
                
                if view.get('assinatura'):
                    content += f"**Assinatura:** ``{view['assinatura']}``\n\n"
                
                if view.get('docstring'):
                    content += "**Descrição:**\n\n"
                    content += f"{view['docstring']}\n\n"
                
                content += "---\n\n"
            
            return content
            
        elif template_name == 'auto_forms.rst':
            content = "Formulários (Gerado Automaticamente)\n"
            content += "=====================================\n\n"
            content += ".. note::\n   Esta documentação foi gerada automaticamente.\n\n"
            
            for form in context.get('forms', []):
                nome = form['nome']
                content += f"{nome}\n"
                content += "-" * len(nome) + "\n\n"
                content += f".. autoclass:: core.forms.{nome}\n"
                content += "   :members:\n"
                content += "   :undoc-members:\n"
                content += "   :show-inheritance:\n\n"
                
                if form.get('docstring'):
                    content += "**Descrição:**\n\n"
                    content += f"{form['docstring']}\n\n"
                
                content += "---\n\n"
            
            return content
            
        elif template_name == 'auto_utils.rst':
            content = "Utilitários (Gerado Automaticamente)\n"
            content += "=====================================\n\n"
            content += ".. note::\n   Esta documentação foi gerada automaticamente.\n\n"
            
            for funcao in context.get('funcoes', []):
                nome = funcao['nome']
                content += f"{nome}\n"
                content += "-" * len(nome) + "\n\n"
                content += f".. autofunction:: core.utils.{nome}\n\n"
                
                if funcao.get('assinatura'):
                    content += f"**Assinatura:** ``{funcao['assinatura']}``\n\n"
                
                if funcao.get('docstring'):
                    content += "**Descrição:**\n\n"
                    content += f"{funcao['docstring']}\n\n"
                
                content += "---\n\n"
            
            return content
            
        elif template_name == 'auto_frontend.rst':
            content = "Frontend (Gerado Automaticamente)\n"
            content += "==================================\n\n"
            content += ".. note::\n   Esta documentação foi gerada automaticamente.\n\n"
            
            content += "Templates\n"
            content += "---------\n\n"
            for template in context.get('templates', []):
                content += f"* **{template['nome']}** - ``{template['caminho']}`` ({template['tamanho']} bytes)\n"
            
            content += "\nArquivos CSS\n"
            content += "------------\n\n"
            for css in context.get('css_files', []):
                content += f"* **{css['nome']}** - ``{css['caminho']}`` ({css['tamanho']} bytes)\n"
                
            content += "\nArquivos JavaScript\n"
            content += "-------------------\n\n"
            for js in context.get('js_files', []):
                content += f"* **{js['nome']}** - ``{js['caminho']}`` ({js['tamanho']} bytes)\n"
            
            return content
        
        # Fallback para templates não reconhecidos
        return f"# {template_name}\n\nTemplate não implementado ainda."

    def _compilar_documentacao(self, formato='html'):
        """Compila documentação usando Sphinx."""
        self.stdout.write(f'🔨 Compilando documentação em formato {formato}...')
        
        # Tentar encontrar sphinx-build
        sphinx_build_cmd = 'sphinx-build'
        
        # No Windows, tentar caminhos alternativos
        import sys
        if sys.platform == 'win32':
            try:
                # Tentar usar o Python atual para executar o módulo sphinx
                import subprocess
                resultado = subprocess.run([
                    sys.executable, '-m', 'sphinx',
                    '-b', formato,
                    str(self.docs_path),
                    str(self.build_path / formato),
                    '-v' if self.verbosity > 1 else '-q'
                ], capture_output=True, text=True, cwd=settings.BASE_DIR)
                
                if resultado.returncode == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Documentação compilada em: {self.build_path / formato}')
                    )
                    if self.verbosity > 1 and resultado.stdout:
                        self.stdout.write(resultado.stdout)
                    return
                else:
                    self.stdout.write(resultado.stderr)
                    
            except Exception as e:
                self.stdout.write(f'Erro ao usar módulo sphinx: {e}')
        
        # Fallback para comando tradicional
        cmd = [
            sphinx_build_cmd,
            '-b', formato,
            str(self.docs_path),
            str(self.build_path / formato)
        ]
        
        if self.verbosity > 1:
            cmd.extend(['-v'])
        else:
            cmd.extend(['-q'])
        
        try:
            resultado = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=settings.BASE_DIR
            )
            
            if resultado.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Documentação compilada em: {self.build_path / formato}')
                )
                if self.verbosity > 1 and resultado.stdout:
                    self.stdout.write(resultado.stdout)
            else:
                raise CommandError(f'Erro na compilação:\n{resultado.stderr}')
                
        except FileNotFoundError:
            raise CommandError('sphinx-build não encontrado. Verifique a instalação do Sphinx.')

    def _abrir_documentacao(self, servidor=False, port=8000):
        """Abre documentação no navegador."""
        import webbrowser
        import time
        
        if servidor:
            # Iniciar servidor HTTP e abrir navegador
            self.stdout.write('🌐 Iniciando servidor HTTP...')
            
            # Verificar se documentação existe
            html_path = self.build_path / 'html'
            if not html_path.exists():
                self.stdout.write(
                    self.style.WARNING('⚠️ Documentação não encontrada. Gerando primeiro...')
                )
                self._compilar_documentacao()
            
            import threading
            import http.server
            import socketserver
            from functools import partial
            
            # Configurar servidor
            os.chdir(html_path)
            handler = partial(http.server.SimpleHTTPRequestHandler)
            
            try:
                with socketserver.TCPServer(("localhost", port), handler) as httpd:
                    url = f"http://localhost:{port}"
                    
                    # Abrir navegador após pequena pausa
                    def abrir_navegador():
                        time.sleep(1)  # Esperar servidor inicializar
                        self.stdout.write(f'🚀 Abrindo documentação em: {url}')
                        webbrowser.open(url)
                    
                    # Abrir navegador em thread separada
                    threading.Thread(target=abrir_navegador, daemon=True).start()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Servidor iniciado em: {url}')
                    )
                    self.stdout.write('📖 Documentação aberta no navegador!')
                    self.stdout.write('⏹️ Pressione Ctrl+C para parar o servidor')
                    
                    # Servidor rodando
                    httpd.serve_forever()
                    
            except KeyboardInterrupt:
                self.stdout.write('\n🛑 Servidor interrompido pelo usuário')
            except OSError as e:
                if "Address already in use" in str(e):
                    self.stdout.write(
                        self.style.ERROR(f'❌ Porta {port} já está em uso. Tente outra porta.')
                    )
                    # Tentar abrir na porta padrão mesmo assim
                    url = f"http://localhost:{port}"
                    self.stdout.write(f'🔗 Tentando abrir: {url}')
                    webbrowser.open(url)
                else:
                    raise
            finally:
                # Voltar ao diretório original
                os.chdir(settings.BASE_DIR)
        else:
            # Apenas abrir arquivo HTML
            html_file = self.build_path / 'html' / 'index.html'
            
            if not html_file.exists():
                self.stdout.write(
                    self.style.WARNING('⚠️ Documentação não encontrada. Gerando primeiro...')
                )
                self._compilar_documentacao()
                
            if html_file.exists():
                file_url = f'file:///{html_file.as_posix()}'
                self.stdout.write(f'🚀 Abrindo documentação: {file_url}')
                webbrowser.open(file_url)
                self.stdout.write(
                    self.style.SUCCESS('✅ Documentação aberta no navegador!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Não foi possível encontrar a documentação.')
                )

    def _modo_watch(self, options):
        """Modo watch: recompila automaticamente quando arquivos mudam."""
        try:
            subprocess.run([
                'sphinx-autobuild',
                str(self.docs_path),
                str(self.build_path / 'html'),
                '--port', str(options['port']),
                '--open-browser'
            ])
        except FileNotFoundError:
            raise CommandError(
                'sphinx-autobuild não encontrado. Instale com: pip install sphinx-autobuild'
            )
        except KeyboardInterrupt:
            self.stdout.write('\n📴 Modo watch parado')

    def _gerar_relatorio_cobertura(self):
        """Gera relatório de cobertura da documentação."""
        try:
            resultado = subprocess.run([
                'sphinx-build',
                '-b', 'coverage',
                str(self.docs_path),
                str(self.build_path / 'coverage')
            ], capture_output=True, text=True)
            
            if resultado.returncode == 0:
                coverage_file = self.build_path / 'coverage' / 'python.txt'
                if coverage_file.exists():
                    self.stdout.write(
                        self.style.SUCCESS('📊 Relatório de cobertura gerado')
                    )
                    return coverage_file.read_text()
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Erro ao gerar relatório de cobertura: {e}')
            )
        
        return None 