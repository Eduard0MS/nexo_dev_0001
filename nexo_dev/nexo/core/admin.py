from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.db import models
from .models import (
    UnidadeCargo,
    Perfil,
    CargoSIORG,
    PlanilhaImportada,
    SimulacaoSalva,
    RelatorioGratificacoes,
    RelatorioOrgaosCentrais,
    RelatorioEfetivo,
    RelatorioGratificacoesPlan1,
    Decreto,
    SolicitacaoRealocacao,
    SolicitacaoPermuta,
    ConfiguracaoRelatorio,
    TipoUsuario,
    SolicitacaoSimulacao,
    NotificacaoSimulacao,
)
from .utils import processa_planilhas
from .siorg_scraper import scrape_siorg
import os
import json
from decimal import Decimal
import math
import sys
from django.contrib.admin.utils import (
    get_deleted_objects as original_get_deleted_objects,
)
from django.db.models.fields.related import ForeignObjectRel
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

# Customização do Admin
admin.site.site_header = "Administração do Nexo"
admin.site.site_title = "Administração do Nexo"
admin.site.index_title = "Administração do Site"

# Funções auxiliares para geração de dados


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
    ORGANOGRAMA_JSON_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "core",
        "static",
        "data",
        "organograma.json",
    )

    print("Iniciando geração do arquivo organograma.json...")

    # Função auxiliar para converter Decimal em float para serialização JSON
    def decimal_para_float(obj):
        if isinstance(obj, Decimal):
            # Arredondar para duas casas decimais
            return round(float(obj), 2)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    # Estrutura para armazenar os dados
    resultado = {"core_unidadecargo": [], "core_cargosiorg": []}

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
            "grafo": unidade.grafo,
        }
        resultado["core_unidadecargo"].append(unidade_dados)

    # Obter todos os registros de CargoSIORG
    cargos_siorg = CargoSIORG.objects.all()
    print(f"Processando {cargos_siorg.count()} registros de CargoSIORG")

    # Adicionar cada cargo ao resultado
    for cargo in cargos_siorg:
        cargo_dados = {"cargo": cargo.cargo, "nivel": cargo.nivel, "valor": cargo.valor}
        resultado["core_cargosiorg"].append(cargo_dados)

    # Salvar o resultado em JSON
    with open(ORGANOGRAMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            resultado, f, ensure_ascii=False, indent=2, default=decimal_para_float
        )

    print(f"Arquivo organograma.json gerado com sucesso em: {ORGANOGRAMA_JSON_PATH}")
    print(
        f"Total de registros: {len(resultado['core_unidadecargo'])} unidades e {len(resultado['core_cargosiorg'])} cargos"
    )

    return True


class ImportPlanilhasForm(forms.Form):
    file_hierarquia = forms.FileField(label="Planilha de Hierarquia")
    file_estrutura_viva = forms.FileField(label="Planilha de Estrutura Viva")

    def clean_file_hierarquia(self):
        file = self.cleaned_data["file_hierarquia"]
        if not file.name.endswith((".csv", ".xlsx")):
            raise forms.ValidationError(
                "O arquivo de hierarquia deve ser CSV ou Excel."
            )
        return file

    def clean_file_estrutura_viva(self):
        file = self.cleaned_data["file_estrutura_viva"]
        if not file.name.endswith((".csv", ".xlsx")):
            raise forms.ValidationError(
                "O arquivo de estrutura viva deve ser CSV ou Excel."
            )
        return file


@admin.register(UnidadeCargo)
class UnidadeCargoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_unidade",
        "denominacao_unidade",
        "tipo_cargo",
        "categoria",
        "nivel",
        "grafo",
    )
    search_fields = ("codigo_unidade", "denominacao_unidade", "tipo_cargo")
    list_filter = ("tipo_cargo", "categoria", "nivel")
    actions = ["limpar_registros_invalidos"]

    def limpar_registros_invalidos(self, request, queryset):
        """Limpa os registros que não possuem grafo válido (não fazem parte da estrutura do ministério)"""
        registros_totais = UnidadeCargo.objects.count()

        # Obter registros sem grafo válido
        registros_invalidos = UnidadeCargo.objects.filter(
            grafo__exact=""
        ) | UnidadeCargo.objects.filter(grafo__isnull=True)
        qtd_invalidos = registros_invalidos.count()

        # Excluir registros inválidos
        registros_invalidos.delete()

        # Exibir mensagem de sucesso
        self.message_user(
            request,
            f"Foram removidos {qtd_invalidos} registros inválidos (sem grafo). Restam {registros_totais - qtd_invalidos} registros válidos no banco de dados.",
            messages.SUCCESS,
        )

    limpar_registros_invalidos.short_description = "Remover registros sem grafo válido"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "import-planilhas/",
                self.admin_site.admin_view(self.import_planilhas_view),
                name="core_unidadecargo_import_planilhas",
            ),
            path(
                "limpar-registros/",
                self.admin_site.admin_view(self.limpar_registros_view),
                name="core_unidadecargo_limpar_registros",
            ),
        ]
        return my_urls + urls

    def limpar_registros_view(self, request):
        """View para limpar registros inválidos"""
        if request.method == "POST":
            registros_totais = UnidadeCargo.objects.count()

            # Obter registros sem grafo válido
            registros_invalidos = UnidadeCargo.objects.filter(
                grafo__exact=""
            ) | UnidadeCargo.objects.filter(grafo__isnull=True)
            qtd_invalidos = registros_invalidos.count()

            # Excluir registros inválidos
            registros_invalidos.delete()

            # Exibir mensagem de sucesso
            self.message_user(
                request,
                f"Foram removidos {qtd_invalidos} registros inválidos (sem grafo). Restam {registros_totais - qtd_invalidos} registros válidos no banco de dados.",
                messages.SUCCESS,
            )

            # Gerar arquivo dados.json após a limpeza
            try:
                gerar_dados_json()
                # Atualizar o organograma (não precisa mais copiar o arquivo)
                atualizar_dados_organograma()
                self.message_user(
                    request,
                    "Arquivo dados.json atualizado com sucesso! O organograma será atualizado automaticamente ao ser visualizado.",
                    messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Erro ao gerar o arquivo dados.json: {str(e)}",
                    messages.ERROR,
                )

            return redirect("..")

        context = {
            "title": "Limpar Registros Inválidos",
            "opts": self.model._meta,
        }
        return render(request, "admin/limpar_registros.html", context)

    def import_planilhas_view(self, request):
        """View para importar planilhas"""
        if request.method == "POST":
            form = ImportPlanilhasForm(request.POST, request.FILES)
            if form.is_valid():
                file_hierarquia = form.cleaned_data["file_hierarquia"]
                file_estrutura_viva = form.cleaned_data["file_estrutura_viva"]

                try:
                    resultado = processa_planilhas(file_hierarquia, file_estrutura_viva)

                    # Gerar arquivo dados.json após a importação
                    try:
                        gerar_dados_json()
                        # Atualizar o organograma
                        atualizar_dados_organograma()
                        self.message_user(
                            request,
                            "Planilhas importadas e dados.json atualizado com sucesso! O organograma será atualizado automaticamente ao ser visualizado.",
                            messages.SUCCESS,
                        )
                    except Exception as e:
                        self.message_user(
                            request,
                            f"Planilhas importadas mas erro ao gerar dados.json: {str(e)}",
                            messages.WARNING,
                        )

                    # Contar quantos registros foram importados
                    total_registros = UnidadeCargo.objects.count()
                    self.message_user(
                        request,
                        f"Importação concluída! Total de registros no banco: {total_registros}",
                        messages.INFO,
                    )

                except Exception as e:
                    self.message_user(
                        request,
                        f"Erro ao processar planilhas: {str(e)}",
                        messages.ERROR,
                    )

                return redirect("..")
        else:
            form = ImportPlanilhasForm()

        context = {
            "form": form,
            "title": "Importar Planilhas",
            "opts": self.model._meta,
        }
        return render(request, "admin/import_planilhas.html", context)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cargo", "departamento", "telefone", "data_atualizacao")
    search_fields = ("usuario__username", "usuario__email", "cargo", "departamento")
    list_filter = ("cargo", "departamento", "data_atualizacao")
    readonly_fields = ("data_atualizacao",)

    fieldsets = (
        ("Informações do Usuário", {"fields": ("usuario", "foto", "telefone")}),
        ("Informações Profissionais", {"fields": ("cargo", "departamento", "bio")}),
        ("Metadados", {"fields": ("data_atualizacao",), "classes": ("collapse",)}),
    )

    def get_deleted_objects(self, objs, request):
        """
        Customiza a mensagem de deleção para evitar erro com usuários que têm caracteres especiais.
        """
        try:
            return original_get_deleted_objects(objs, request.user, self.admin_site)
        except Exception as e:
            # Em caso de erro, retorna uma mensagem simples
            deleted_objects = []
            model_count = {}
            perms_needed = set()
            protected = []

            for obj in objs:
                deleted_objects.append(f"Perfil: {obj}")
                model_count[obj._meta.verbose_name_plural] = len(objs)

            return deleted_objects, model_count, perms_needed, protected


@admin.register(CargoSIORG)
class CargoSIORGAdmin(admin.ModelAdmin):
    list_display = (
        "cargo",
        "nivel",
        "quantidade",
        "valor",
        "unitario",
        "data_atualizacao",
    )
    search_fields = ("cargo", "nivel")
    list_filter = ("nivel", "data_atualizacao")
    readonly_fields = ("data_atualizacao",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "scrape-siorg/",
                self.admin_site.admin_view(self.scrape_siorg_view),
                name="core_cargosiorg_scrape",
            ),
        ]
        return my_urls + urls

    def scrape_siorg_view(self, request):
        if request.method == "POST":
            try:
                cargos = scrape_siorg()
                for cargo_data in cargos:
                    CargoSIORG.objects.update_or_create(
                        cargo=cargo_data["cargo"],
                        nivel=cargo_data["nivel"],
                        defaults={
                            "quantidade": cargo_data["quantidade"],
                            "valor": cargo_data["valor"],
                            "unitario": cargo_data["unitario"],
                        },
                    )

                self.message_user(
                    request,
                    f"{len(cargos)} cargos foram importados com sucesso!",
                    messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request, f"Erro ao importar cargos: {str(e)}", messages.ERROR
                )

            return redirect("..")

        context = {
            "title": "Importar Cargos do SIORG",
            "opts": self.model._meta,
        }
        return render(request, "admin/scrape_siorg.html", context)


# Registrar o admin customizado para User
class CustomUserAdmin(BaseUserAdmin):
    """Admin customizado para User que lida com caracteres especiais"""

    def get_deleted_objects(self, objs, request):
        """
        Customiza a mensagem de deleção para evitar erro com usuários que têm caracteres especiais.
        """
        deleted_objects = []
        model_count = {}
        perms_needed = set()
        protected = []

        for obj in objs:
            # Criar uma representação segura do objeto
            def custom_format_callback(obj):
                try:
                    if hasattr(obj, "username"):
                        username = (
                            obj.username if obj.username != "-" else f"Usuário {obj.id}"
                        )
                        return f"Usuário: {username}"
                    else:
                        return str(obj)
                except:
                    return f"Objeto {obj.__class__.__name__}"

            try:
                # Tentar o método original primeiro
                (
                    deleted_objects_orig,
                    model_count_orig,
                    perms_needed_orig,
                    protected_orig,
                ) = original_get_deleted_objects([obj], request.user, self.admin_site)
                deleted_objects.extend(deleted_objects_orig)
                model_count.update(model_count_orig)
                perms_needed.update(perms_needed_orig)
                protected.extend(protected_orig)
            except Exception as e:
                # Em caso de erro, usar nossa representação customizada
                deleted_objects.append(custom_format_callback(obj))

                # Contar objetos relacionados manualmente
                related_objects = []
                for field in obj._meta.get_fields():
                    if (
                        isinstance(field, ForeignObjectRel)
                        and field.on_delete != models.DO_NOTHING
                    ):
                        try:
                            related_manager = getattr(obj, field.get_accessor_name())
                            related_count = related_manager.count()
                            if related_count > 0:
                                related_objects.append(
                                    f"{field.related_model._meta.verbose_name_plural}: {related_count}"
                                )
                        except:
                            pass

                if related_objects:
                    deleted_objects.extend(related_objects)

                model_count[obj._meta.verbose_name_plural] = 1

        return deleted_objects, model_count, perms_needed, protected


# Desregistrar o admin padrão e registrar o customizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(PlanilhaImportada)
class PlanilhaImportadaAdmin(admin.ModelAdmin):
    list_display = ("nome", "arquivo", "data_importacao", "ativo")
    search_fields = ("nome",)
    list_filter = ("data_importacao", "ativo")
    readonly_fields = ("data_importacao",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_planilha_view),
                name="core_planilhaimportada_importar",
            ),
        ]
        return my_urls + urls

    def importar_planilha_view(self, request):
        if request.method == "POST":
            form = ImportarPlanilhaForm(request.POST, request.FILES)
            if form.is_valid():
                planilha = form.save()
                self.message_user(
                    request,
                    f'Planilha "{planilha.nome}" importada com sucesso!',
                    messages.SUCCESS,
                )
                return redirect("..")
        else:
            form = ImportarPlanilhaForm()

        context = {
            "form": form,
            "title": "Importar Nova Planilha",
            "opts": self.model._meta,
        }
        return render(request, "admin/importar_planilha.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        return super().changelist_view(request, extra_context)


class ImportarPlanilhaForm(forms.Form):
    nome = forms.CharField(max_length=255, label="Nome da Planilha")
    arquivo = forms.FileField(label="Arquivo Excel")
    ativo = forms.BooleanField(
        label="Definir como Planilha Ativa", required=False, initial=False
    )


@admin.register(SimulacaoSalva)
class SimulacaoSalvaAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "usuario",
        "status",
        "tipo_usuario",
        "visivel_para_gerentes",
        "unidade_base",
        "criado_em",
        "atualizado_em",
    ]
    list_filter = [
        "status",
        "tipo_usuario",
        "visivel_para_gerentes",
        "usuario",
        "unidade_base",
        "criado_em",
    ]
    search_fields = ["nome", "descricao", "usuario__username", "usuario__email"]
    readonly_fields = ["criado_em", "atualizado_em"]

    fieldsets = (
        ("Informações da Simulação", {"fields": ("nome", "descricao", "unidade_base")}),
        (
            "Status e Controle",
            {"fields": ("status", "tipo_usuario", "visivel_para_gerentes")},
        ),
        (
            "Dados da Simulação",
            {"fields": ("dados_estrutura",), "classes": ("collapse",)},
        ),
        (
            "Informações do Sistema",
            {
                "fields": ("usuario", "criado_em", "atualizado_em"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(usuario=request.user)
        return qs

    def has_add_permission(self, request):
        # Apenas superusuários podem adicionar diretamente pelo admin
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Superusuários podem editar qualquer simulação
        if request.user.is_superuser:
            return True
        # Usuários normais só podem editar suas próprias simulações
        if obj is not None:
            return obj.usuario == request.user
        return True

    def has_delete_permission(self, request, obj=None):
        # Apenas superusuários podem deletar
        return request.user.is_superuser


# === FORMULÁRIOS PARA IMPORTAÇÃO ===


class ImportarGratificacoesForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de Lotações (Aba: Planilha1)",
        help_text='Arquivo Excel (.xlsx ou .xls) - será importada automaticamente a aba "Planilha1" com dados de servidores e lotações',
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.endswith((".xlsx", ".xls")):
            raise forms.ValidationError(
                "O arquivo deve ser uma planilha Excel (.xlsx ou .xls)."
            )
        return arquivo


class ImportarOrgaosForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de Órgãos",
        help_text="Arquivo Excel (.xlsx ou .xls) com dados de órgãos centrais e setoriais",
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.endswith((".xlsx", ".xls")):
            raise forms.ValidationError(
                "O arquivo deve ser uma planilha Excel (.xlsx ou .xls)."
            )
        return arquivo


class ImportarGratificacoesPlan1Form(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de Gratificações (Aba: Plan1)",
        help_text='Arquivo Excel (.xlsx ou .xls) - será importada automaticamente a aba "Plan1" com dados de gratificações por órgão',
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.endswith((".xlsx", ".xls")):
            raise forms.ValidationError(
                "O arquivo deve ser uma planilha Excel (.xlsx ou .xls)."
            )
        return arquivo


class ImportarEfetivoForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de Efetivo",
        help_text="Arquivo Excel (.xlsx ou .xls) com dados de efetivo",
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.endswith((".xlsx", ".xls")):
            raise forms.ValidationError(
                "O arquivo deve ser uma planilha Excel (.xlsx ou .xls)."
            )
        return arquivo


# === ADMINS PARA RELATÓRIOS ===


@admin.register(RelatorioGratificacoes)
class RelatorioGratificacoesAdmin(admin.ModelAdmin):
    list_display = (
        "nome_servidor",
        "matricula_siape",
        "cargo",
        "unidade_lotacao",
        "secretaria_lotacao",
        "data_importacao",
    )
    list_filter = (
        "cargo",
        "situacao_funcional",
        "secretaria_lotacao",
        "uf",
        "data_importacao",
    )
    search_fields = (
        "nome_servidor",
        "matricula_siape",
        "cargo",
        "unidade_lotacao",
        "email_institucional",
    )
    readonly_fields = ("data_importacao",)
    actions = ["limpar_todos_registros"]

    def limpar_todos_registros(self, request, queryset):
        """Ação para limpar todos os registros da tabela"""
        total = RelatorioGratificacoes.objects.count()
        RelatorioGratificacoes.objects.all().delete()
        self.message_user(
            request,
            f"✅ Todos os {total} registros de gratificações foram removidos com sucesso!",
            messages.SUCCESS,
        )

    limpar_todos_registros.short_description = (
        "🗑️ Limpar TODOS os registros de gratificações"
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name="core_relatoriogratificacoes_importar",
            ),
        ]
        return my_urls + urls

    def importar_view(self, request):
        if request.method == "POST":
            form = ImportarGratificacoesForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Processar arquivo e salvar dados - APENAS aba Planilha1
                    arquivo = form.cleaned_data["arquivo"]

                    print(f"=== INICIANDO PROCESSAMENTO DO ARQUIVO: {arquivo.name} ===")
                    print(
                        "=== Importando APENAS aba 'Planilha1' (dados de servidores/lotações) ==="
                    )

                    # Limpar dados anteriores antes de importar
                    registros_anteriores = RelatorioGratificacoes.objects.count()
                    if registros_anteriores > 0:
                        RelatorioGratificacoes.objects.all().delete()
                        print(
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas"
                        )
                        self.message_user(
                            request,
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas.",
                            messages.INFO,
                        )

                    resultado = self.processar_planilha_gratificacoes(
                        arquivo, "Planilha1"
                    )

                    if resultado["inseridos"] > 0:
                        self.message_user(
                            request,
                            f'✅ Importação concluída! {resultado["inseridos"]} registros de servidores inseridos da aba "Planilha1".',
                            messages.SUCCESS,
                        )
                    else:
                        self.message_user(
                            request,
                            f'⚠️ Nenhum registro foi inserido da aba "Planilha1". Verifique se a planilha tem essa aba com dados de servidores.',
                            messages.WARNING,
                        )

                    if resultado["erros"]:
                        self.message_user(
                            request,
                            f'⚠️ {len(resultado["erros"])} erro(s) encontrado(s): {resultado["erros"][:3]}',
                            messages.WARNING,
                        )

                except Exception as e:
                    error_msg = f"Erro ao processar arquivo: {str(e)}"
                    print(f"ERRO CRÍTICO: {error_msg}")
                    import traceback

                    traceback.print_exc()
                    self.message_user(request, error_msg, messages.ERROR)

                return redirect("..")
        else:
            form = ImportarGratificacoesForm()

        context = {
            "form": form,
            "title": "Importar Dados de Servidores (Aba: Planilha1)",
            "opts": self.model._meta,
        }
        return render(request, "admin/importar_gratificacoes.html", context)

    def processar_planilha_gratificacoes(self, arquivo, nome_aba=None):
        import pandas as pd
        from datetime import datetime

        try:
            # Ler o arquivo Excel
            print(f"Lendo arquivo Excel: {arquivo.name}")
            if nome_aba:
                print(f"Aba especificada: {nome_aba}")
                df = pd.read_excel(arquivo, sheet_name=nome_aba)
            else:
                df = pd.read_excel(arquivo)
            print(f"Arquivo lido com sucesso. Shape: {df.shape}")

            # Log das colunas para debug
            print(f"Colunas encontradas na planilha: {list(df.columns)}")
            print(
                f"Primeira linha de dados: {df.iloc[0].to_dict() if len(df) > 0 else 'VAZIA'}"
            )

            if df.empty:
                return {"inseridos": 0, "erros": ["A planilha está vazia"]}

            # Função auxiliar para buscar valores considerando possíveis variações nas colunas
            def obter_valor(row, possiveis_nomes):
                for nome in possiveis_nomes:
                    if nome in df.columns and nome in row and pd.notna(row[nome]):
                        valor = str(row[nome]).strip()
                        if valor and valor != "nan" and valor != "None":
                            return valor
                return ""

            inseridos = 0
            erros = []
            linhas_processadas = 0

            print(f"Iniciando processamento de {len(df)} linhas...")

            for index, row in df.iterrows():
                linhas_processadas += 1
                print(f"Processando linha {index + 1}...")

                try:
                    # Processar data de nascimento
                    data_nascimento = None
                    data_valor = obter_valor(row, ["Data de Nascimento"])
                    if data_valor:
                        try:
                            data_nascimento = pd.to_datetime(
                                data_valor, errors="coerce"
                            )
                        except:
                            pass

                    # Processar idade
                    idade = None
                    idade_valor = obter_valor(row, ["Idade"])
                    if idade_valor:
                        try:
                            idade = int(float(idade_valor))
                        except:
                            pass

                    # Extrair valores principais para debug
                    nome = obter_valor(row, ["Nome do Servidor"])
                    matricula = obter_valor(row, ["Matrícula SIAPE"])
                    cargo = obter_valor(row, ["Cargo"])

                    print(
                        f"Linha {index + 1}: Nome={nome}, Matricula={matricula}, Cargo={cargo}"
                    )

                    # Criar o registro
                    registro = RelatorioGratificacoes.objects.create(
                        nome_servidor=nome,
                        matricula_siape=matricula,
                        situacao_funcional=obter_valor(row, ["Situação Funcional"]),
                        cargo=cargo,
                        nivel=obter_valor(row, ["Nível"]),
                        gsiste=obter_valor(row, ["Gsiste"]),
                        gsiste_nivel=obter_valor(row, ["Gsiste Nível"]),
                        funcao=obter_valor(row, ["Função"]),
                        nivel_funcao=obter_valor(row, ["Nível da Função"]),
                        atividade_funcao=obter_valor(row, ["Atividade da Função"]),
                        jornada_trabalho=obter_valor(row, ["Jornada de Trabalho"]),
                        unidade_lotacao=obter_valor(row, ["Unidade de Lotação"]),
                        secretaria_lotacao=obter_valor(row, ["Secretaria da Lotação"]),
                        uf=obter_valor(row, ["UF"]),
                        uorg_exercicio=obter_valor(row, ["UORG de Exercício"]),
                        unidade_exercicio=obter_valor(row, ["Unidade de Exercício"]),
                        coordenacao=obter_valor(row, ["Coordenação"]),
                        diretoria=obter_valor(row, ["Diretoria"]),
                        secretaria=obter_valor(row, ["Secretaria"]),
                        orgao_origem=obter_valor(row, ["Órgão Origem"]),
                        email_institucional=obter_valor(row, ["e-Mail Institucional"]),
                        siape_titular_chefe=obter_valor(
                            row, ["Siape do Titular Chefe"]
                        ),
                        siape_substituto=obter_valor(row, ["Siape do Substituto"]),
                    )
                    inseridos += 1
                    print(
                        f"Registro {inseridos} criado com sucesso (ID: {registro.id})"
                    )

                except Exception as e:
                    erro_msg = f"Linha {index + 2}: {str(e)}"
                    erros.append(erro_msg)
                    print(f"ERRO na linha {index + 2}: {str(e)}")
                    print(f"Dados da linha: {dict(row)}")

            print(
                f"Processamento concluído. {inseridos} inseridos de {linhas_processadas} processadas."
            )
            return {"inseridos": inseridos, "erros": erros}

        except Exception as e:
            print(f"ERRO ao ler arquivo: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"inseridos": 0, "erros": [f"Erro ao ler arquivo: {str(e)}"]}

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        return super().changelist_view(request, extra_context)


@admin.register(RelatorioOrgaosCentrais)
class RelatorioOrgaosCentraisAdmin(admin.ModelAdmin):
    list_display = (
        "tipo_orgao",
        "nivel_cargo",
        "valor_maximo",
        "efeitos_financeiros_data",
        "data_importacao",
    )
    list_filter = ("tipo_orgao", "data_importacao")
    search_fields = ("nivel_cargo",)
    readonly_fields = ("data_importacao",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name="core_relatorioorgaoscentrais_importar",
            ),
        ]
        return my_urls + urls

    def importar_view(self, request):
        if request.method == "POST":
            form = ImportarOrgaosForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Processar arquivo e salvar dados
                    arquivo = form.cleaned_data["arquivo"]
                    resultado = self.processar_planilha_orgaos(arquivo)

                    self.message_user(
                        request,
                        f'Importação concluída! {resultado["inseridos"]} registros inseridos.',
                        messages.SUCCESS,
                    )
                    if resultado["erros"]:
                        self.message_user(
                            request,
                            f'{len(resultado["erros"])} erro(s) encontrado(s). Verifique o log.',
                            messages.WARNING,
                        )

                except Exception as e:
                    self.message_user(
                        request, f"Erro ao processar arquivo: {str(e)}", messages.ERROR
                    )

                return redirect("..")
        else:
            form = ImportarOrgaosForm()

        context = {
            "form": form,
            "title": "Importar Planilha de Órgãos",
            "opts": self.model._meta,
        }
        return render(request, "admin/importar_orgaos.html", context)

    def processar_planilha_orgaos(self, arquivo):
        import pandas as pd
        from decimal import Decimal

        # Ler o arquivo Excel
        df = pd.read_excel(arquivo)

        inseridos = 0
        erros = []

        for index, row in df.iterrows():
            try:
                # Determinar tipo de órgão baseado no conteúdo
                tipo_orgao = (
                    "central"
                    if "central" in str(row.get("Tipo", "")).lower()
                    else "setorial"
                )

                RelatorioOrgaosCentrais.objects.create(
                    tipo_orgao=tipo_orgao,
                    nivel_cargo=row.get("Nível do Cargo", ""),
                    valor_maximo=Decimal(
                        str(row.get("Valor Máximo da GSISTE", 0))
                        .replace(",", ".")
                        .replace("R$", "")
                        .strip()
                    ),
                    efeitos_financeiros_data=row.get(
                        "Efeitos Financeiros a partir de", ""
                    ),
                )
                inseridos += 1
            except Exception as e:
                erros.append(f"Linha {index + 2}: {str(e)}")

        return {"inseridos": inseridos, "erros": erros}

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        return super().changelist_view(request, extra_context)


@admin.register(RelatorioEfetivo)
class RelatorioEfetivoAdmin(admin.ModelAdmin):
    list_display = (
        "ordem_planilha",
        "qt",
        "nome_completo",
        "funcao",
        "unidade_macro",
        "horario",
        "data_importacao",
    )
    list_filter = ("funcao", "unidade_macro", "data_importacao")
    search_fields = ("nome_completo", "funcao", "unidade_macro")
    readonly_fields = ("data_importacao",)
    actions = ["limpar_todos_registros"]
    change_list_template = "admin/change_list_with_import.html"

    def limpar_todos_registros(self, request, queryset):
        """Ação para limpar todos os registros da tabela"""
        total = RelatorioEfetivo.objects.count()
        RelatorioEfetivo.objects.all().delete()
        self.message_user(
            request,
            f"✅ Todos os {total} registros de efetivo foram removidos com sucesso!",
            messages.SUCCESS,
        )

    limpar_todos_registros.short_description = "🗑️ Limpar TODOS os registros de efetivo"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name="core_relatorioefetivo_importar",
            ),
        ]
        return my_urls + urls

    def importar_view(self, request):
        if request.method == "POST":
            form = ImportarEfetivoForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Processar arquivo e salvar dados
                    arquivo = form.cleaned_data["arquivo"]

                    print(f"=== INICIANDO PROCESSAMENTO DO ARQUIVO: {arquivo.name} ===")
                    print("=== Importando dados de efetivo ===")

                    # Limpar dados anteriores antes de importar
                    registros_anteriores = RelatorioEfetivo.objects.count()
                    if registros_anteriores > 0:
                        RelatorioEfetivo.objects.all().delete()
                        print(
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas"
                        )
                        self.message_user(
                            request,
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas.",
                            messages.INFO,
                        )

                    resultado = self.processar_planilha_efetivo(arquivo)

                    if resultado["inseridos"] > 0:
                        self.message_user(
                            request,
                            f'✅ Importação concluída! {resultado["inseridos"]} registros de efetivo inseridos.',
                            messages.SUCCESS,
                        )
                    else:
                        self.message_user(
                            request,
                            f"⚠️ Nenhum registro foi inserido. Verifique se a planilha tem dados válidos.",
                            messages.WARNING,
                        )

                    if resultado["erros"]:
                        self.message_user(
                            request,
                            f'⚠️ {len(resultado["erros"])} erro(s) encontrado(s): {resultado["erros"][:3]}',
                            messages.WARNING,
                        )

                except Exception as e:
                    error_msg = f"Erro ao processar arquivo: {str(e)}"
                    print(f"ERRO CRÍTICO: {error_msg}")
                    import traceback

                    traceback.print_exc()
                    self.message_user(request, error_msg, messages.ERROR)

                return redirect("..")
        else:
            form = ImportarEfetivoForm()

        context = {
            "form": form,
            "title": "Importar Planilha de Efetivo",
            "opts": self.model._meta,
        }
        return render(request, "admin/importar_efetivo.html", context)

    def processar_planilha_efetivo(self, arquivo):
        import pandas as pd
        from datetime import datetime

        try:
            # Ler o arquivo Excel
            print(f"Lendo arquivo Excel: {arquivo.name}")
            df = pd.read_excel(arquivo)
            print(f"Arquivo lido com sucesso. Shape: {df.shape}")
            print(f"Colunas encontradas: {list(df.columns)}")

            inseridos = 0
            erros = []

            for index, row in df.iterrows():
                try:
                    print(f"Processando linha {index + 1} da planilha...")

                    # Ler dados EXATAMENTE como estão na planilha, sem modificar nada
                    qt_original = row.iloc[0] if len(row) > 0 else ""
                    nome_original = row.iloc[1] if len(row) > 1 else ""
                    funcao_original = row.iloc[2] if len(row) > 2 else ""
                    unidade_original = row.iloc[3] if len(row) > 3 else ""
                    horario_original = row.iloc[4] if len(row) > 4 else ""
                    bloco_original = row.iloc[5] if len(row) > 5 else ""

                    # Converter para string, preservando valores vazios
                    qt_str = str(qt_original).strip() if pd.notna(qt_original) else ""
                    nome_str = (
                        str(nome_original).strip() if pd.notna(nome_original) else ""
                    )
                    funcao_str = (
                        str(funcao_original).strip()
                        if pd.notna(funcao_original)
                        else ""
                    )
                    unidade_str = (
                        str(unidade_original).strip()
                        if pd.notna(unidade_original)
                        else ""
                    )
                    horario_str = (
                        str(horario_original).strip()
                        if pd.notna(horario_original)
                        else ""
                    )
                    bloco_str = (
                        str(bloco_original).strip() if pd.notna(bloco_original) else ""
                    )

                    print(
                        f"📋 Linha {index + 1} da planilha - Coluna A (QT): '{qt_str}' | Nome: '{nome_str}' | Função: '{funcao_str}'"
                    )

                    # Pular apenas linhas que são claramente cabeçalhos
                    if nome_str.upper() in ["NOME COMPLETO", "NOME"]:
                        print(f"Linha {index + 1}: Cabeçalho detectado, pulando...")
                        continue

                    # Pular linhas completamente vazias
                    if not any(
                        [
                            qt_str,
                            nome_str,
                            funcao_str,
                            unidade_str,
                            horario_str,
                            bloco_str,
                        ]
                    ):
                        print(f"Linha {index + 1}: Linha vazia, pulando...")
                        continue

                    # Usar o valor QT EXATAMENTE como está na planilha
                    if qt_str and qt_str.upper() != "QT":
                        try:
                            qt_final = int(float(qt_str))
                        except:
                            qt_final = 0
                    else:
                        qt_final = 0

                    # Criar registro com dados EXATOS da planilha
                    RelatorioEfetivo.objects.create(
                        ordem_planilha=index + 1,  # Preserva ordem exata da planilha
                        qt=qt_final,
                        nome_completo=nome_str,
                        funcao=funcao_str,
                        unidade_macro=unidade_str,
                        horario=horario_str,
                        bloco_andar=bloco_str,
                        data_importacao=datetime.now(),
                    )

                    inseridos += 1
                    print(
                        f"✅ Registro {inseridos} salvo: QT={qt_final} (valor literal da coluna A) | Nome: {nome_str} | Função: {funcao_str}"
                    )

                except Exception as e:
                    erro_msg = f"Linha {index + 1}: {str(e)}"
                    erros.append(erro_msg)
                    print(f"ERRO na linha {index + 1}: {str(e)}")

            print(f"Processamento concluído. {inseridos} inseridos.")
            return {"inseridos": inseridos, "erros": erros}

        except Exception as e:
            print(f"ERRO ao ler arquivo: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"inseridos": 0, "erros": [f"Erro ao ler arquivo: {str(e)}"]}

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        return super().changelist_view(request, extra_context)


@admin.register(RelatorioGratificacoesPlan1)
class RelatorioGratificacoesPlan1Admin(admin.ModelAdmin):
    list_display = (
        "tipo_orgao",
        "nivel_cargo",
        "valor_maximo_gsiste",
        "efeitos_financeiros_data",
        "data_importacao",
    )
    list_filter = ("tipo_orgao", "data_importacao")
    search_fields = ("nivel_cargo",)
    readonly_fields = ("data_importacao",)
    actions = ["limpar_todos_registros"]
    change_list_template = "admin/change_list_with_import.html"

    def limpar_todos_registros(self, request, queryset):
        """Ação para limpar todos os registros da tabela"""
        total = RelatorioGratificacoesPlan1.objects.count()
        RelatorioGratificacoesPlan1.objects.all().delete()
        self.message_user(
            request,
            f"✅ Todos os {total} registros de gratificações por órgão foram removidos com sucesso!",
            messages.SUCCESS,
        )

    limpar_todos_registros.short_description = (
        "🗑️ Limpar TODOS os registros de gratificações por órgão"
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name="core_relatoriogratificacoesplan1_importar",
            ),
        ]
        return my_urls + urls

    def importar_view(self, request):
        if request.method == "POST":
            form = ImportarGratificacoesPlan1Form(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Processar arquivo e salvar dados - APENAS aba Plan1
                    arquivo = form.cleaned_data["arquivo"]

                    print(f"=== INICIANDO PROCESSAMENTO DO ARQUIVO: {arquivo.name} ===")
                    print(
                        "=== Importando APENAS aba 'Plan1' (dados de gratificações por órgão) ==="
                    )

                    # Limpar dados anteriores antes de importar
                    registros_anteriores = RelatorioGratificacoesPlan1.objects.count()
                    if registros_anteriores > 0:
                        RelatorioGratificacoesPlan1.objects.all().delete()
                        print(
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas"
                        )
                        self.message_user(
                            request,
                            f"🗑️ Removidos {registros_anteriores} registros anteriores para evitar duplicatas.",
                            messages.INFO,
                        )

                    resultado = self.processar_planilha_plan1(arquivo)

                    if resultado["inseridos"] > 0:
                        self.message_user(
                            request,
                            f'✅ Importação concluída! {resultado["inseridos"]} registros de gratificações inseridos da aba "Plan1".',
                            messages.SUCCESS,
                        )
                    else:
                        self.message_user(
                            request,
                            f'⚠️ Nenhum registro foi inserido da aba "Plan1". Verifique se a planilha tem essa aba com dados de gratificações.',
                            messages.WARNING,
                        )

                    if resultado["erros"]:
                        self.message_user(
                            request,
                            f'⚠️ {len(resultado["erros"])} erro(s) encontrado(s): {resultado["erros"][:3]}',
                            messages.WARNING,
                        )

                except Exception as e:
                    error_msg = f"Erro ao processar arquivo: {str(e)}"
                    print(f"ERRO CRÍTICO: {error_msg}")
                    import traceback

                    traceback.print_exc()
                    self.message_user(request, error_msg, messages.ERROR)

                return redirect("..")
        else:
            form = ImportarGratificacoesPlan1Form()

        context = {
            "form": form,
            "title": "Importar Gratificações por Órgão (Aba: Plan1)",
            "opts": self.model._meta,
        }
        return render(request, "admin/importar_gratificacoes_plan1.html", context)

    def processar_planilha_plan1(self, arquivo):
        import pandas as pd
        from decimal import Decimal
        from datetime import datetime

        try:
            # Ler o arquivo Excel - aba Plan1
            print(f"Lendo arquivo Excel: {arquivo.name} - Aba: Plan1")
            df = pd.read_excel(arquivo, sheet_name="Plan1")
            print(f"Arquivo lido com sucesso. Shape: {df.shape}")
            print(f"Colunas encontradas na planilha: {list(df.columns)}")

            if df.empty:
                return {"inseridos": 0, "erros": ["A aba Plan1 está vazia"]}

            inseridos = 0
            erros = []

            # Detectar tipo de órgão atual
            tipo_atual = None

            for index, row in df.iterrows():
                try:
                    print(f"Processando linha {index + 1}...")

                    # Detectar se é cabeçalho de seção
                    primeira_coluna = (
                        str(row.iloc[0]).strip().upper()
                        if not pd.isna(row.iloc[0])
                        else ""
                    )

                    if "ÓRGÃOS CENTRAIS" in primeira_coluna:
                        tipo_atual = "central"
                        print(f"Linha {index + 1}: Detectado seção ÓRGÃOS CENTRAIS")
                        continue
                    elif "ÓRGÃOS SETORIAIS" in primeira_coluna:
                        tipo_atual = "setorial"
                        print(f"Linha {index + 1}: Detectado seção ÓRGÃOS SETORIAIS")
                        continue
                    elif "LIMITES GSISTE" in primeira_coluna:
                        tipo_atual = "limites"
                        print(f"Linha {index + 1}: Detectado seção LIMITES GSISTE")
                        continue

                    # Pular linhas de cabeçalho, informativas ou vazias
                    if (
                        not tipo_atual
                        or "NÍVEL DO CARGO" in primeira_coluna
                        or primeira_coluna == ""
                        or "LIMITES" == primeira_coluna  # Linha 23
                        or "EXCLUÍDAS" in primeira_coluna  # Linha 24
                        or "VALOR MÁXIMO" in primeira_coluna  # Cabeçalhos
                        or "EFEITOS FINANCEIROS" in primeira_coluna
                    ):  # Cabeçalhos
                        continue

                    # Buscar dados nas colunas
                    nivel_cargo = (
                        str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
                    )
                    valor_str = (
                        str(row.iloc[1]).strip()
                        if len(row) > 1 and not pd.isna(row.iloc[1])
                        else "0"
                    )

                    # Validar se tem dados válidos
                    if (
                        not nivel_cargo
                        or nivel_cargo in ["nan", "None", "", "NÍVEL DO CARGO"]
                        or valor_str
                        in ["nan", "None", "", "0", "VALOR MÁXIMO DA GSISTE"]
                    ):
                        continue

                    # Converter valor simples (formato brasileiro: 2.203,98 -> 2203.98)
                    try:
                        # Remover 'R$' e espaços
                        valor_limpo = valor_str.replace("R$", "").strip()

                        # Formato brasileiro: substituir vírgula por ponto e remover pontos de milhares
                        if "," in valor_limpo:
                            # Tem vírgula decimal: remover pontos de milhares, trocar vírgula por ponto
                            valor_final = valor_limpo.replace(".", "").replace(",", ".")
                        else:
                            # Sem vírgula: usar valor como está (pode ser inteiro)
                            valor_final = valor_limpo

                        valor_maximo = Decimal(valor_final)
                        print(
                            f"Valor convertido: '{valor_str}' -> '{valor_final}' -> {valor_maximo}"
                        )
                    except Exception as e:
                        print(f"Erro ao converter valor '{valor_str}': {e}")
                        valor_maximo = Decimal("0.00")

                    # Criar registro
                    RelatorioGratificacoesPlan1.objects.create(
                        tipo_orgao=tipo_atual,
                        nivel_cargo=nivel_cargo,
                        valor_maximo_gsiste=valor_maximo,
                        efeitos_financeiros_data="1º DE MAIO DE 2023",
                        data_importacao=datetime.now(),
                    )

                    inseridos += 1
                    print(
                        f"Registro {inseridos} criado: {tipo_atual} - {nivel_cargo} - R$ {valor_maximo}"
                    )

                except Exception as e:
                    erro_msg = f"Linha {index + 1}: {str(e)}"
                    erros.append(erro_msg)
                    print(f"ERRO na linha {index + 1}: {str(e)}")

            print(f"Processamento concluído. {inseridos} inseridos.")
            return {"inseridos": inseridos, "erros": erros}

        except Exception as e:
            print(f"ERRO ao ler arquivo: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"inseridos": 0, "erros": [f"Erro ao ler arquivo: {str(e)}"]}

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        return super().changelist_view(request, extra_context)


# === ADMIN PARA NOVOS MODELOS DO SISTEMA DE RELATÓRIOS ===


@admin.register(Decreto)
class DecretoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "data_publicacao",
        "titulo_resumido",
        "tipo",
        "status",
        "data_cadastro",
    )
    list_filter = ("tipo", "status", "data_publicacao", "data_cadastro")
    search_fields = ("numero", "titulo")
    readonly_fields = ("data_cadastro",)
    date_hierarchy = "data_publicacao"

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("numero", "data_publicacao", "titulo", "tipo", "status")},
        ),
        ("Documentação", {"fields": ("arquivo", "observacoes")}),
        (
            "Controle",
            {"fields": ("usuario_cadastro", "data_cadastro"), "classes": ("collapse",)},
        ),
    )

    def titulo_resumido(self, obj):
        return obj.titulo[:100] + "..." if len(obj.titulo) > 100 else obj.titulo

    titulo_resumido.short_description = "Título"

    def save_model(self, request, obj, form, change):
        if not change:  # Se está criando um novo objeto
            obj.usuario_cadastro = request.user
        super().save_model(request, obj, form, change)


@admin.register(SolicitacaoRealocacao)
class SolicitacaoRealocacaoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_servidor",
        "matricula_siape",
        "unidade_atual",
        "unidade_destino",
        "status",
        "data_solicitacao",
    )
    list_filter = ("status", "data_solicitacao", "unidade_atual", "unidade_destino")
    search_fields = (
        "nome_servidor",
        "matricula_siape",
        "unidade_atual",
        "unidade_destino",
    )
    readonly_fields = ("data_solicitacao", "usuario_solicitante")
    date_hierarchy = "data_solicitacao"

    fieldsets = (
        ("Informações do Servidor", {"fields": ("nome_servidor", "matricula_siape")}),
        (
            "Realocação",
            {"fields": ("unidade_atual", "unidade_destino", "justificativa")},
        ),
        (
            "Status e Análise",
            {
                "fields": (
                    "status",
                    "data_analise",
                    "usuario_analista",
                    "observacoes_analise",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": ("usuario_solicitante", "data_solicitacao"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status != "pendente":
            # Se já foi analisada, tornar alguns campos readonly
            readonly.extend(
                ["nome_servidor", "matricula_siape", "unidade_atual", "unidade_destino"]
            )
        return readonly

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            # Se o status mudou, registrar data e usuário da análise
            if obj.status in ["aprovada", "rejeitada"]:
                obj.data_analise = timezone.now()
                obj.usuario_analista = request.user
        super().save_model(request, obj, form, change)


@admin.register(SolicitacaoPermuta)
class SolicitacaoPermutaAdmin(admin.ModelAdmin):
    list_display = (
        "nome_servidor1",
        "nome_servidor2",
        "unidade_servidor1",
        "unidade_servidor2",
        "status",
        "data_solicitacao",
    )
    list_filter = (
        "status",
        "data_solicitacao",
        "unidade_servidor1",
        "unidade_servidor2",
    )
    search_fields = (
        "nome_servidor1",
        "nome_servidor2",
        "matricula_servidor1",
        "matricula_servidor2",
    )
    readonly_fields = ("data_solicitacao", "usuario_solicitante")
    date_hierarchy = "data_solicitacao"

    fieldsets = (
        (
            "Servidor 1",
            {"fields": ("nome_servidor1", "matricula_servidor1", "unidade_servidor1")},
        ),
        (
            "Servidor 2",
            {"fields": ("nome_servidor2", "matricula_servidor2", "unidade_servidor2")},
        ),
        ("Informações da Permuta", {"fields": ("observacoes",)}),
        (
            "Status e Análise",
            {
                "fields": (
                    "status",
                    "data_analise",
                    "usuario_analista",
                    "observacoes_analise",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": ("usuario_solicitante", "data_solicitacao"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status != "pendente":
            # Se já foi analisada, tornar alguns campos readonly
            readonly.extend(
                [
                    "nome_servidor1",
                    "nome_servidor2",
                    "matricula_servidor1",
                    "matricula_servidor2",
                ]
            )
        return readonly

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            # Se o status mudou, registrar data e usuário da análise
            if obj.status in ["aprovada", "rejeitada"]:
                obj.data_analise = timezone.now()
                obj.usuario_analista = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfiguracaoRelatorio)
class ConfiguracaoRelatorioAdmin(admin.ModelAdmin):
    list_display = (
        "chave",
        "valor_resumido",
        "descricao",
        "data_atualizacao",
        "usuario_atualizacao",
    )
    list_filter = ("data_atualizacao", "usuario_atualizacao")
    search_fields = ("chave", "descricao", "valor")
    readonly_fields = ("data_atualizacao",)

    fieldsets = (
        ("Configuração", {"fields": ("chave", "valor", "descricao")}),
        (
            "Controle",
            {
                "fields": ("usuario_atualizacao", "data_atualizacao"),
                "classes": ("collapse",),
            },
        ),
    )

    def valor_resumido(self, obj):
        return obj.valor[:50] + "..." if len(obj.valor) > 50 else obj.valor

    valor_resumido.short_description = "Valor"

    def save_model(self, request, obj, form, change):
        if not change:  # Se é uma nova configuração
            obj.usuario_atualizacao = request.user
        super().save_model(request, obj, form, change)


# === ADMINS PARA SISTEMA DE TRÊS NÍVEIS DE USUÁRIOS ===


@admin.register(TipoUsuario)
class TipoUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "tipo",
        "pode_solicitar",
        "pode_ver_todas",
        "ativo",
        "criado_em",
        "atualizado_em",
    )
    list_filter = ("tipo", "pode_solicitar", "pode_ver_todas", "ativo", "criado_em")
    search_fields = (
        "usuario__username",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
    )
    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        ("Usuário", {"fields": ("usuario",)}),
        (
            "Configurações de Acesso",
            {"fields": ("tipo", "pode_solicitar", "pode_ver_todas", "ativo")},
        ),
        (
            "Informações do Sistema",
            {"fields": ("criado_em", "atualizado_em"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Usuários não-superuser só veem seus próprios tipos
            qs = qs.filter(usuario=request.user)
        return qs


@admin.register(SolicitacaoSimulacao)
class SolicitacaoSimulacaoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "solicitante",
        "usuario_designado",
        "prioridade",
        "status",
        "criada_em",
        "aceita_em",
    )
    list_filter = ("status", "prioridade", "criada_em", "aceita_em")
    search_fields = (
        "titulo",
        "descricao",
        "solicitante__username",
        "usuario_designado__username",
        "unidade_base_sugerida",
    )
    readonly_fields = ("criada_em", "atualizada_em")
    date_hierarchy = "criada_em"

    fieldsets = (
        (
            "Informações da Solicitação",
            {
                "fields": (
                    "titulo",
                    "descricao",
                    "unidade_base_sugerida",
                    "prazo_estimado",
                    "prioridade",
                )
            },
        ),
        ("Usuários Envolvidos", {"fields": ("solicitante", "usuario_designado")}),
        (
            "Status e Progresso",
            {
                "fields": (
                    "status",
                    "aceita_em",
                    "simulacao_criada",
                    "observacoes_usuario",
                )
            },
        ),
        (
            "Informações do Sistema",
            {"fields": ("criada_em", "atualizada_em"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Usuários não-superuser só veem solicitações onde estão envolvidos
            qs = qs.filter(
                Q(solicitante=request.user) | Q(usuario_designado=request.user)
            )
        return qs

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)

        # Se não é superuser, restringir algumas alterações
        if not request.user.is_superuser:
            if obj and obj.solicitante != request.user:
                # Se não é o solicitante, não pode alterar dados básicos
                readonly.extend(
                    [
                        "titulo",
                        "descricao",
                        "unidade_base_sugerida",
                        "prazo_estimado",
                        "prioridade",
                        "solicitante",
                        "usuario_designado",
                    ]
                )

        return readonly

    def save_model(self, request, obj, form, change):
        if not change:  # Se é uma nova solicitação
            obj.solicitante = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotificacaoSimulacao)
class NotificacaoSimulacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "tipo", "lida", "criada_em")
    list_filter = ("tipo", "lida", "criada_em")
    search_fields = ("titulo", "mensagem", "usuario__username", "usuario__email")
    readonly_fields = ("criada_em",)
    date_hierarchy = "criada_em"

    fieldsets = (
        ("Notificação", {"fields": ("usuario", "tipo", "titulo", "mensagem", "lida")}),
        (
            "Relacionamentos",
            {"fields": ("solicitacao", "simulacao"), "classes": ("collapse",)},
        ),
        (
            "Informações do Sistema",
            {"fields": ("criada_em",), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Usuários não-superuser só veem suas próprias notificações
            qs = qs.filter(usuario=request.user)
        return qs

    def has_add_permission(self, request):
        # Apenas superusuários podem criar notificações manualmente
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Usuários podem marcar suas notificações como lidas
        if request.user.is_superuser:
            return True
        if obj is not None:
            return obj.usuario == request.user
        return True

    def has_delete_permission(self, request, obj=None):
        # Apenas superusuários podem deletar notificações
        return request.user.is_superuser


# Registrar customizações existentes
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Registrar outros modelos que não têm @admin.register
# (Todos os modelos agora usam @admin.register decorators)
