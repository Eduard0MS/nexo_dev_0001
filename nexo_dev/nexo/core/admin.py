from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from .models import UnidadeCargo, Perfil, CargoSIORG, PlanilhaImportada, SimulacaoSalva
from .utils import processa_planilhas
from .siorg_scraper import scrape_siorg
import os
import json
from decimal import Decimal
import math
import sys
from django.contrib.admin.utils import get_deleted_objects as original_get_deleted_objects
from django.db.models.fields.related import ForeignObjectRel
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Customização do Admin
admin.site.site_header = "Administração do Nexo"
admin.site.site_title = "Administração do Nexo"
admin.site.index_title = "Administração do Site"

# Importar a função de geração do arquivo JSON
try:
    from gerar_dados_json import gerar_dados_json
    from atualizar_dados_organograma import atualizar_dados_organograma
except ImportError:
    # Função para atualizar os dados do organograma
    def atualizar_dados_organograma():
        """Atualiza o arquivo organograma.json a partir do dados.json."""
        try:
            # Não é mais necessário copiar o arquivo, já que
            # o organograma agora acessa o dados.json diretamente via API
            print("Organograma será atualizado via API ao ser carregado")
            return True
        except Exception as e:
            print(f"Erro ao atualizar organograma: {str(e)}")
            return False
            
    # Função para gerar o arquivo dados.json
    def gerar_dados_json():
        """
        Gera um arquivo JSON com dados das tabelas UnidadeCargo e CargoSIORG.
        O arquivo será salvo como organograma.json.
        """
        import os
        import json
        from decimal import Decimal
        from .models import UnidadeCargo, CargoSIORG
        
        # Caminho para o arquivo de saída
        ORGANOGRAMA_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core', 'static', 'data', 'organograma.json')
        
        print("Iniciando geração do arquivo organograma.json...")
        
        # Função auxiliar para converter Decimal em float para serialização JSON
        def decimal_para_float(obj):
            if isinstance(obj, Decimal):
                # Arredondar para duas casas decimais
                return round(float(obj), 2)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Estrutura para armazenar os dados
        resultado = {
            "core_unidadecargo": [],
            "core_cargosiorg": []
        }
        
        # Obter todos os registros de UnidadeCargo
        unidades_cargo = UnidadeCargo.objects.all()
        print(f"Processando {unidades_cargo.count()} registros de UnidadeCargo")
        
        # Adicionar cada unidade de cargo ao resultado
        for unidade in unidades_cargo:
            unidade_dados = {
                "tipo_unidade": unidade.tipo_unidade,
                "denominacao_unidade": unidade.denominacao_unidade,
                "codigo_unidade": unidade.codigo_unidade,
                "sigla": unidade.sigla_unidade,
                "tipo_cargo": unidade.tipo_cargo,
                "denominacao": unidade.denominacao,
                "categoria": unidade.categoria,
                "nivel": unidade.nivel,
                "quantidade": unidade.quantidade,
                "grafo": unidade.grafo
            }
            resultado["core_unidadecargo"].append(unidade_dados)
        
        # Obter todos os registros de CargoSIORG
        cargos_siorg = CargoSIORG.objects.all()
        print(f"Processando {cargos_siorg.count()} registros de CargoSIORG")
        
        # Adicionar cada cargo ao resultado
        for cargo in cargos_siorg:
            cargo_dados = {
                "cargo": cargo.cargo,
                "nivel": cargo.nivel,
                "valor": cargo.valor
            }
            resultado["core_cargosiorg"].append(cargo_dados)
        
        # Salvar o resultado em JSON
        with open(ORGANOGRAMA_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2, default=decimal_para_float)
        
        print(f"Arquivo organograma.json gerado com sucesso em: {ORGANOGRAMA_JSON_PATH}")
        print(f"Total de registros: {len(resultado['core_unidadecargo'])} unidades e {len(resultado['core_cargosiorg'])} cargos")
        
        return True

class ImportPlanilhasForm(forms.Form):
    file_hierarquia = forms.FileField(label='Planilha de Hierarquia')
    file_estrutura_viva = forms.FileField(label='Planilha de Estrutura Viva')

    def clean_file_hierarquia(self):
        file = self.cleaned_data['file_hierarquia']
        if not file.name.endswith(('.csv', '.xlsx')):
            raise forms.ValidationError("O arquivo de hierarquia deve ser CSV ou Excel.")
        return file

    def clean_file_estrutura_viva(self):
        file = self.cleaned_data['file_estrutura_viva']
        if not file.name.endswith(('.csv', '.xlsx')):
            raise forms.ValidationError("O arquivo de estrutura viva deve ser CSV ou Excel.")
        return file

@admin.register(UnidadeCargo)
class UnidadeCargoAdmin(admin.ModelAdmin):
    list_display = ('codigo_unidade', 'denominacao_unidade', 'tipo_cargo', 'categoria', 'nivel', 'grafo')
    search_fields = ('codigo_unidade', 'denominacao_unidade', 'tipo_cargo')
    list_filter = ('tipo_cargo', 'categoria', 'nivel')
    actions = ['limpar_registros_invalidos']
    
    def limpar_registros_invalidos(self, request, queryset):
        """Limpa os registros que não possuem grafo válido (não fazem parte da estrutura do ministério)"""
        registros_totais = UnidadeCargo.objects.count()
        
        # Obter registros sem grafo válido
        registros_invalidos = UnidadeCargo.objects.filter(grafo__exact='') | UnidadeCargo.objects.filter(grafo__isnull=True)
        qtd_invalidos = registros_invalidos.count()
        
        # Excluir registros inválidos
        registros_invalidos.delete()
        
        # Exibir mensagem de sucesso
        self.message_user(
            request, 
            f'Foram removidos {qtd_invalidos} registros inválidos (sem grafo). Restam {registros_totais - qtd_invalidos} registros válidos no banco de dados.',
            messages.SUCCESS
        )
    
    limpar_registros_invalidos.short_description = "Remover registros sem grafo válido"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                'import-planilhas/',
                self.admin_site.admin_view(self.import_planilhas_view),
                name='core_unidadecargo_import_planilhas'
            ),
            path(
                'limpar-registros/',
                self.admin_site.admin_view(self.limpar_registros_view),
                name='core_unidadecargo_limpar_registros'
            ),
        ]
        return my_urls + urls
    
    def limpar_registros_view(self, request):
        """View para limpar registros inválidos"""
        if request.method == 'POST':
            registros_totais = UnidadeCargo.objects.count()
            
            # Obter registros sem grafo válido
            registros_invalidos = UnidadeCargo.objects.filter(grafo__exact='') | UnidadeCargo.objects.filter(grafo__isnull=True)
            qtd_invalidos = registros_invalidos.count()
            
            # Excluir registros inválidos
            registros_invalidos.delete()
            
            # Exibir mensagem de sucesso
            self.message_user(
                request, 
                f'Foram removidos {qtd_invalidos} registros inválidos (sem grafo). Restam {registros_totais - qtd_invalidos} registros válidos no banco de dados.',
                messages.SUCCESS
            )
            
            # Gerar arquivo dados.json após a limpeza
            try:
                gerar_dados_json()
                # Atualizar o organograma (não precisa mais copiar o arquivo)
                atualizar_dados_organograma()
                self.message_user(
                    request,
                    'Arquivo dados.json atualizado com sucesso! O organograma será atualizado automaticamente ao ser visualizado.',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Erro ao gerar arquivo dados.json: {str(e)}',
                    messages.ERROR
                )
            
            return redirect('..')
        
        return render(request, 'admin/limpar_registros.html', {
            'title': 'Limpar Registros Inválidos',
            'opts': self.model._meta,
        })

    def import_planilhas_view(self, request):
        if request.method == 'POST':
            form = ImportPlanilhasForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Processar planilhas usando a função do utils.py
                    df_resultado = processa_planilhas(
                        form.cleaned_data['file_hierarquia'],
                        form.cleaned_data['file_estrutura_viva']
                    )
                    
                    # Limpar a tabela antes de inserir novos registros
                    UnidadeCargo.objects.all().delete()
                    
                    # Contador para registros processados e registros válidos
                    total_registros = len(df_resultado)
                    registros_importados = 0
                    
                    # Inserir os dados no banco de dados
                    for _, row in df_resultado.iterrows():
                        # Verificar se o grafo é válido antes de importar
                        grafo = row.get('Grafo', '')
                        if not grafo or grafo.strip() == '':
                            continue  # Pular registros sem grafo válido
                            
                        # Criar o objeto UnidadeCargo
                        UnidadeCargo.objects.create(
                            nivel_hierarquico=row.get('Nível Hierárquico', 0),
                            tipo_unidade=row.get('Tipo Unidade', ''),
                            denominacao_unidade=row.get('Deno Unidade', ''),
                            codigo_unidade=row.get('Código Unidade', ''),
                            sigla_unidade=row.get('Sigla Unidade', ''),
                            categoria_unidade=row.get('Categoria Unidade', ''),
                            orgao_entidade=row.get('Órgão/Entidade', ''),
                            tipo_cargo=row.get('Tipo do Cargo', ''),
                            denominacao=row.get('Denominação', ''),
                            complemento_denominacao=row.get('Complemento Denominação', ''),
                            categoria=row.get('Categoria', 0),
                            nivel=row.get('Nível', 0),
                            quantidade=row.get('Quantidade', 0),
                            grafo=grafo,
                            sigla=row.get('Sigla', '')
                        )
                        registros_importados += 1
                    
                    # Após a importação, limpar quaisquer registros inválidos que possam ter entrado
                    registros_invalidos = UnidadeCargo.objects.filter(grafo__exact='') | UnidadeCargo.objects.filter(grafo__isnull=True)
                    qtd_invalidos = registros_invalidos.count()
                    if qtd_invalidos > 0:
                        registros_invalidos.delete()
                        mensagem_extra = f" Foram removidos {qtd_invalidos} registros inválidos adicionais."
                    else:
                        mensagem_extra = ""
                    
                    # Gerar arquivo dados.json após a importação
                    try:
                        gerar_dados_json()
                        # Atualizar o organograma (não precisa mais copiar o arquivo)
                        atualizar_dados_organograma()
                        mensagem_dados_json = " Arquivo dados.json atualizado com sucesso! O organograma será atualizado automaticamente ao ser visualizado."
                    except Exception as e:
                        mensagem_dados_json = f" Erro ao gerar arquivo dados.json: {str(e)}"
                    
                    self.message_user(
                        request, 
                        f'Planilhas importadas com sucesso! {registros_importados} de {total_registros} registros foram importados.{mensagem_extra}{mensagem_dados_json}', 
                        messages.SUCCESS
                    )
                    return redirect('..')
                except Exception as e:
                    self.message_user(request, f'Erro ao importar planilhas: {str(e)}', messages.ERROR)
            else:
                self.message_user(request, 'Por favor, corrija os erros no formulário.', messages.ERROR)
        else:
            form = ImportPlanilhasForm()
        
        return render(request, 'admin/import_planilhas.html', {
            'form': form,
            'title': 'Importar Planilhas de Estrutura',
            'opts': self.model._meta,
        })

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cargo', 'departamento', 'telefone', 'data_atualizacao')
    search_fields = ('usuario__username', 'usuario__email', 'cargo', 'departamento')
    list_filter = ('cargo', 'departamento', 'data_atualizacao')
    readonly_fields = ('data_atualizacao',)
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('usuario', 'foto')
        }),
        ('Informações Profissionais', {
            'fields': ('cargo', 'departamento', 'telefone')
        }),
        ('Informações Adicionais', {
            'fields': ('bio', 'data_atualizacao')
        }),
    )
    
    def get_deleted_objects(self, objs, request):
        """
        Método personalizado para lidar com a exclusão de perfis que pode conter campos 
        problemáticos como usernames vazios ou com caracteres especiais
        """
        try:
            # Tentar usar o método padrão
            return original_get_deleted_objects(objs, request, self.admin_site)
        except Exception as e:
            # Em caso de falha, implementar uma versão simplificada
            # que ignora erros de string no __str__
            collector = admin.utils.NestedObjects(using='default')
            collector.collect(objs)
            perms_needed = set()
            protected = set()
            model_count = {model._meta.verbose_name_plural: len(objs_list) for model, objs_list in collector.model_objs.items()}
            
            return collector.nested(), model_count, perms_needed, protected

@admin.register(CargoSIORG)
class CargoSIORGAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'nivel', 'quantidade', 'valor', 'unitario', 'data_atualizacao')
    search_fields = ('cargo', 'nivel')
    list_filter = ('nivel', 'data_atualizacao')
    readonly_fields = ('data_atualizacao',)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                'scrape-siorg/',
                self.admin_site.admin_view(self.scrape_siorg_view),
                name='core_cargosiorg_scrape'
            ),
        ]
        return my_urls + urls

    def scrape_siorg_view(self, request):
        if request.method == 'POST':
            result = scrape_siorg()
            if result['success']:
                # Gerar arquivo dados.json após a atualização do SIORG
                try:
                    gerar_dados_json()
                    # Atualizar o organograma (não precisa mais copiar o arquivo)
                    atualizar_dados_organograma()
                    self.message_user(
                        request, 
                        f"{result['message']} Arquivo dados.json atualizado com sucesso! O organograma será atualizado automaticamente ao ser visualizado.", 
                        level=messages.SUCCESS
                    )
                except Exception as e:
                    self.message_user(
                        request, 
                        f"{result['message']} Erro ao gerar arquivo dados.json: {str(e)}", 
                        level=messages.WARNING
                    )
            else:
                self.message_user(request, result['message'], level=messages.ERROR)
            return redirect('..')
        return render(request, 'admin/scrape_siorg.html', {
            'opts': self.model._meta,
            'title': "Atualizar Dados do SIORG"
        })

# Classe personalizada para o admin de User do Django
class CustomUserAdmin(BaseUserAdmin):
    """
    Classe de administração personalizada para o modelo User nativo do Django,
    sobrescrevendo métodos de exclusão para lidar com situações específicas.
    """
    def get_deleted_objects(self, objs, request):
        """
        Método personalizado para lidar com a exclusão de usuários que pode conter
        relacionamentos com objetos que têm __str__ problemáticos
        """
        try:
            # Tentar usar o método padrão
            return original_get_deleted_objects(objs, request, self.admin_site)
        except Exception as e:
            # Em caso de falha, implementar uma versão simplificada
            # com um format_callback personalizado
            from django.contrib.admin.utils import NestedObjects
            from django.utils.text import capfirst
            
            collector = NestedObjects(using='default')
            collector.collect(objs)
            
            def custom_format_callback(obj):
                try:
                    opts = obj._meta
                    # Para usuários, usar o ID em vez do username se o username for problemático
                    if isinstance(obj, User) and (not obj.username or obj.username == "-"):
                        return "%s: %s" % (capfirst(opts.verbose_name), f"ID: {obj.id}")
                    return "%s: %s" % (capfirst(opts.verbose_name), str(obj))
                except Exception:
                    # Se houver qualquer problema, retornar uma string segura
                    return "Objeto de Tipo %s (ID: %s)" % (obj.__class__.__name__, obj.pk)
            
            perms_needed = set()
            protected = set()
            
            # Usar o formato personalizado para criar a estrutura aninhada
            to_delete = collector.nested(custom_format_callback)
            
            # Criar um dicionário de contagem de modelo manualmente
            model_count = {}
            for model, objs_list in collector.model_objs.items():
                key = str(model._meta.verbose_name_plural)
                model_count[key] = len(objs_list)
            
            return to_delete, model_count, perms_needed, protected

# Desregistrar o admin padrão de User
admin.site.unregister(User)

# Registrar nosso admin personalizado
admin.site.register(User, CustomUserAdmin)

@admin.register(PlanilhaImportada)
class PlanilhaImportadaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'arquivo', 'data_importacao', 'ativo')
    search_fields = ('nome',)
    list_filter = ('data_importacao', 'ativo')
    readonly_fields = ('data_importacao',)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('importar-planilha/', self.admin_site.admin_view(self.importar_planilha_view), name='importar_planilha'),
        ]
        return my_urls + urls

    def importar_planilha_view(self, request):
        if request.method == 'POST':
            form = ImportarPlanilhaForm(request.POST, request.FILES)
            if form.is_valid():
                planilha = PlanilhaImportada(
                    nome=form.cleaned_data['nome'],
                    arquivo=form.cleaned_data['arquivo'],
                    ativo=form.cleaned_data['ativo']
                )
                planilha.save()
                self.message_user(request, 'Planilha importada com sucesso!', messages.SUCCESS)
                return redirect('..')
        else:
            form = ImportarPlanilhaForm()
        
        return render(request, 'admin/importar_planilha.html', {
            'form': form,
            'title': 'Importar Planilha',
            'opts': self.model._meta,
        })

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

class ImportarPlanilhaForm(forms.Form):
    nome = forms.CharField(max_length=255, label='Nome da Planilha')
    arquivo = forms.FileField(label='Arquivo Excel')
    ativo = forms.BooleanField(label='Definir como Planilha Ativa', required=False, initial=False)

@admin.register(SimulacaoSalva)
class SimulacaoSalvaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'usuario', 'unidade_base', 'criado_em', 'atualizado_em']
    list_filter = ['usuario', 'unidade_base', 'criado_em']
    search_fields = ['nome', 'descricao', 'usuario__username', 'usuario__email']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'nome', 'descricao', 'unidade_base')
        }),
        ('Dados da Simulação', {
            'fields': ('dados_estrutura',),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('usuario')
    
    def has_add_permission(self, request):
        # Apenas superusuários podem adicionar diretamente pelo admin
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Superusuários podem editar qualquer simulação
        if request.user.is_superuser:
            return True
        # Usuários regulares não têm acesso ao admin
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Apenas superusuários podem deletar
        return request.user.is_superuser
