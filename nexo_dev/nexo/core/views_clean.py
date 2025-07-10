# core/views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .forms import (
    CustomLoginForm,
    CustomRegisterForm,
    DualFileUploadForm,
    FileUploadForm,
    UserUpdateForm,
    PerfilUpdateForm,
    CustomPasswordChangeForm,
)
from .models import UnidadeCargo, CargoSIORG
from .utils import (
    processa_planilhas,
    processa_organograma,
    estrutura_json_organograma,
    processa_json_organograma,
)
import os
from django.conf import settings
import json
from django.contrib import messages
from allauth.account.views import SignupView
from allauth.socialaccount.views import SignupView as SocialSignupView
import csv
import io
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .financeira_export import (
    dados_financeiros_backup,
    exportar_csv_simples,
    exportar_html_simples,
)
import random
from datetime import datetime
from .models import Perfil
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods
from decimal import Decimal


class CustomLoginView(LoginView):
    template_name = "registration/login_direct.html"
    authentication_form = CustomLoginForm
    success_url = reverse_lazy("home")
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("home")

    def form_invalid(self, form):
        # Implementar rate limiting apenas em produção
        if not settings.DEBUG:
            ip = self.request.META.get("REMOTE_ADDR")
            cache_key = f"login_attempts_{ip}"
            attempts = cache.get(cache_key, 0)

            if attempts >= 5:
                return HttpResponseForbidden(
                    "Muitas tentativas de login. Tente novamente em 15 minutos."
                )

            cache.set(cache_key, attempts + 1, 900)  # 15 minutos
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_authenticated:
            return response
        return self.form_invalid(form)


@csrf_protect
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
    else:
        form = CustomRegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required(login_url="/login_direct/")
def home(request, form=None):
    return render(request, "home.html", {"form": form})


@login_required
def view_organograma(request):
    """Renderiza a página do organograma."""
    return render(request, "core/organograma.html")


@login_required
def organograma_page(request):
    """Renderiza a página do organograma."""
    return render(request, "core/organograma.html")


@require_http_methods(["GET"])
def organograma_redirect(request):
    """View para redirecionar da URL original do organograma para a nova visualização"""
    return render(request, "organograma_redirect.html")


@login_required
def organograma_data(request):
    """
    Retorna os dados do organograma em formato JSON hierárquico.
    """
    from .utils import estrutura_json_organograma

    try:
        dados = estrutura_json_organograma()
        if not dados:
            return JsonResponse({"error": "Nenhuma unidade encontrada"})
        return JsonResponse(dados)
    except Exception as e:
        return JsonResponse({"error": f"Erro ao processar dados: {str(e)}"}, status=500)


@login_required
def organograma_view(request):
    """Renderiza a página do organograma."""
    return render(request, "core/organograma.html")


@login_required(login_url="/login_direct/")
def simulacao_page(request):
    """
    View que renderiza a página de simulação do organograma
    onde o usuário pode adicionar nomes e criar conexões manualmente.
    """
    return render(request, "core/simulacao.html")


@login_required(login_url="/login_direct/")
def financeira_page(request):
    """
    View que renderiza a página financeira com integração
    direta com o organograma e simulação.
    """
    return render(request, "core/financeira.html")


@login_required(login_url="/login_direct/")
def financeira_data(request):
    """
    Retorna dados financeiros em formato JSON.
    Se o período for especificado, filtra os dados para o período correto.
    """

    # Obtém o período da requisição (dia, semana, mes, ano, personalizado)
    periodo = request.GET.get("periodo", "mes")

    try:
        # Para simular dados diferentes por período
        orcamento_base = 1825000.00  # Orçamento base de R$ 1.825.000,00
        executado_base = 950000.00  # Executado base de R$ 950.000,00

        # Ajuste dependendo do período
        multiplicador = {
            "dia": 0.033,  # 1/30 do valor mensal
            "semana": 0.25,  # 1/4 do valor mensal
            "mes": 1.0,  # Valor mensal completo
            "ano": 12.0,  # 12x o valor mensal
            "personalizado": 3.5,  # Valor personalizado (exemplo: trimestre)
        }

        multiplicador_atual = multiplicador.get(periodo, 1.0)
        orcamento = orcamento_base * multiplicador_atual
        executado = executado_base * multiplicador_atual

        # Percentual de execução (executado / orçamento)
        percentual = (executado / orcamento) * 100 if orcamento > 0 else 0

        # Status baseado no percentual
        status = (
            "Crítico"
            if percentual < 50
            else ("Atenção" if percentual < 80 else "Adequado")
        )

        # Dados para o gráfico com um mês extra para projeção (se período for mensal)
        labels = []
        orcado = []
        realizado = []

        # Gera dados para o gráfico dependendo do período
        if periodo == "dia":
            # Últimos 10 dias
            for i in range(10):
                labels.append(f"Dia {i+1}")
                orcado.append(
                    round(orcamento_base * 0.033 * (0.9 + 0.2 * random.random()), 2)
                )
                realizado.append(
                    round(executado_base * 0.033 * (0.85 + 0.3 * random.random()), 2)
                )
        elif periodo == "semana":
            # Últimas 8 semanas
            for i in range(8):
                labels.append(f"Semana {i+1}")
                orcado.append(
                    round(orcamento_base * 0.25 * (0.9 + 0.2 * random.random()), 2)
                )
                realizado.append(
                    round(executado_base * 0.25 * (0.85 + 0.3 * random.random()), 2)
                )
        elif periodo == "mes":
            # Últimos 6 meses + 1 projetado
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho"]
            for i in range(7):
                labels.append(meses[i])
                if i < 6:  # Meses passados
                    orcado.append(
                        round(orcamento_base * (0.9 + 0.2 * random.random()), 2)
                    )
                    realizado.append(
                        round(executado_base * (0.85 + 0.3 * random.random()), 2)
                    )
                else:  # Mês projetado
                    orcado.append(round(orcamento_base * 1.05, 2))
                    realizado.append(
                        0
                    )  # Valor zero para projeção, mais seguro que None
        elif periodo == "ano":
            # Últimos 5 anos + 1 projetado
            atual = datetime.now().year
            for i in range(6):
                year = atual - 5 + i
                labels.append(str(year))
                if i < 5:  # Anos passados
                    orcado.append(
                        round(orcamento_base * 12 * (0.9 + 0.2 * random.random()), 2)
                    )
                    realizado.append(
                        round(executado_base * 12 * (0.85 + 0.3 * random.random()), 2)
                    )
                else:  # Ano projetado
                    orcado.append(round(orcamento_base * 12 * 1.05, 2))
                    realizado.append(
                        0
                    )  # Valor zero para projeção, mais seguro que None
        else:  # personalizado
            # 12 períodos personalizados
            for i in range(12):
                labels.append(f"Período {i+1}")
                orcado.append(
                    round(orcamento_base * 3.5 * (0.9 + 0.2 * random.random()) / 12, 2)
                )
                realizado.append(
                    round(executado_base * 3.5 * (0.85 + 0.3 * random.random()) / 12, 2)
                )

        # Preparação dos dados para execução mensal
        execucao_mensal = []
        for i in range(len(labels)):
            # Verificação de segurança para não ter valores None ou inválidos
            valor_orcado = orcado[i] if orcado[i] is not None else 0
            valor_realizado = (
                realizado[i] if i < len(realizado) and realizado[i] is not None else 0
            )

            execucao_mensal.append(
                {"mes": labels[i], "orcado": valor_orcado, "executado": valor_realizado}
            )

        # Prepara dados para organograma financeiro (unidades e seus dados financeiros)
        unidades_financeiras = [
            {
                "codigo": "PM001",
                "nome": "Presidência",
                "orcamento": round(orcamento * 0.05, 2),  # 5% do orçamento total
                "executado": round(executado * 0.04, 2),  # 4% do executado total
                "percentual": 80.0,
                "status": "Adequado",
            },
            {
                "codigo": "ADM001",
                "nome": "Diretoria Administrativa",
                "orcamento": round(orcamento * 0.15, 2),  # 15% do orçamento total
                "executado": round(executado * 0.13, 2),  # 13% do executado total
                "percentual": 86.7,
                "status": "Adequado",
            },
            {
                "codigo": "FIN001",
                "nome": "Diretoria Financeira",
                "orcamento": round(orcamento * 0.10, 2),
                "executado": round(executado * 0.09, 2),
                "percentual": 90.0,
                "status": "Adequado",
            },
            {
                "codigo": "RH001",
                "nome": "Departamento RH",
                "orcamento": round(orcamento * 0.08, 2),
                "executado": round(executado * 0.085, 2),
                "percentual": 10.3,
                "status": "Crítico",
            },
            {
                "codigo": "CMP001",
                "nome": "Departamento Compras",
                "orcamento": round(orcamento * 0.07, 2),
                "executado": round(executado * 0.045, 2),
                "percentual": 64.3,
                "status": "Atenção",
            },
            {
                "codigo": "SAU001",
                "nome": "Setor Saúde",
                "orcamento": round(orcamento * 0.40, 2),
                "executado": round(executado * 0.25, 2),
                "percentual": 62.5,
                "status": "Atenção",
            },
        ]

        # Preparação dos dados de resposta
        dados = {
            "orcamento_total": orcamento,
            "executado_total": executado,
            "percentual_execucao": percentual,
            "status": status,
            "variacao_periodo": (
                12.5 if periodo == "mes" else 8.7
            ),  # Simulação de variação
            "unidades": unidades_financeiras,
            "execucao_mensal": execucao_mensal,
            "periodo": periodo,
        }

        return JsonResponse(dados)

    except Exception as e:
        # Log do erro
        print(f"Erro ao processar dados financeiros: {str(e)}")

        # Retorna dados de backup em caso de erro
        backup_data = dados_financeiros_backup(periodo)
        return JsonResponse(backup_data)


# Função para fornecer dados de backup em caso de erro
def dados_financeiros_backup(periodo="mes"):
    """Gera dados financeiros de backup para uso em caso de falha"""
    try:
        # Valores base de backup
        orcamento = 2450000.00
        executado = 1320500.00
        percentual = 54.0
        status = "Atenção"

        # Unidades simplificadas
        unidades = [
            {
                "codigo": "PM001",
                "nome": "Presidência",
                "orcamento": round(orcamento * 0.05, 2),
                "executado": round(executado * 0.04, 2),
                "percentual": 80.0,
                "status": "Adequado",
            },
            {
                "codigo": "ADM001",
                "nome": "Diretoria Administrativa",
                "orcamento": round(orcamento * 0.15, 2),
                "executado": round(executado * 0.13, 2),
                "percentual": 86.7,
                "status": "Adequado",
            },
            {
                "codigo": "FIN001",
                "nome": "Diretoria Financeira",
                "orcamento": round(orcamento * 0.10, 2),
                "executado": round(executado * 0.09, 2),
                "percentual": 90.0,
                "status": "Adequado",
            },
        ]

        # Dados de execução simplificados
        execucao_mensal = []
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho"]

        for i, mes in enumerate(meses):
            execucao_mensal.append(
                {
                    "mes": mes,
                    "orcado": round(orcamento / 6, 2),
                    "executado": round(executado / 6, 2),
                }
            )

        return {
            "orcamento_total": orcamento,
            "executado_total": executado,
            "percentual_execucao": percentual,
            "status": status,
            "variacao_periodo": 12.5,
            "unidades": unidades,
            "execucao_mensal": execucao_mensal,
            "periodo": periodo,
            "is_backup_data": True,
        }
    except Exception as e:
        # Se mesmo o backup falhar, retorne o mínimo possível
        print(f"Erro nos dados de backup: {str(e)}")
        return {
            "orcamento_total": 2000000.00,
            "executado_total": 1000000.00,
            "percentual_execucao": 50.0,
            "status": "Atenção",
            "is_backup_data": True,
            "error_message": "Dados mínimos de contingência",
        }


@login_required(login_url="/login_direct/")
def financeira_export(request):
    """
    Exporta dados financeiros em diferentes formatos: PDF, CSV, XLSX, HTML
    """
    try:
        # Processar parâmetros do request
        formato = request.GET.get("formato", "html")
        periodo = request.GET.get("periodo", "Mês Atual")
        componente = request.GET.get("componente", "completo")

        # Obter dados financeiros
        # Reutilização da lógica de financeira_data
        try:
            response = financeira_data(request)
            if response.status_code == 200:
                dados = json.loads(response.content)
                dados["titulo"] = "Relatório Financeiro"
                dados["periodo"] = periodo
            else:
                # Usar dados de backup
                dados = dados_financeiros_backup()
        except Exception:
            # Em caso de erro, usar dados de backup
            dados = dados_financeiros_backup()

        # Filtrar dados conforme o componente solicitado
        if componente == "resumo":
            dados_filtrados = {
                "orcamento_total": dados["orcamento_total"],
                "executado_total": dados["executado_total"],
                "variacao_periodo": dados["variacao_periodo"],
                "titulo": "Resumo Financeiro",
                "periodo": periodo,
            }
        elif componente == "distribuicao":
            dados_filtrados = {
                "unidades": dados["unidades"],
                "titulo": "Distribuição por Unidade",
                "periodo": periodo,
            }
        elif componente == "execucao":
            dados_filtrados = {
                "execucao_mensal": dados["execucao_mensal"],
                "titulo": "Execução Orçamentária",
                "periodo": periodo,
            }
        else:  # completo
            dados_filtrados = dados

        # Exportar conforme o formato
        try:
            if formato == "csv":
                return exportar_csv(dados_filtrados, componente)
            elif formato == "xlsx":
                return exportar_xlsx(dados_filtrados, componente)
            elif formato == "pdf":
                return exportar_pdf(dados_filtrados, componente)
            else:  # html
                return exportar_html(dados_filtrados, componente)
        except Exception as e:
            # Em caso de falha na exportação, usar versões simplificadas de backup
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao exportar dados no formato {formato}: {e}")

            if formato == "csv":
                return exportar_csv_simples(dados_filtrados, componente)
            elif formato == "xlsx":
                # Para XLSX, retornar CSV como fallback
                return exportar_csv_simples(dados_filtrados, componente)
            elif formato == "pdf":
                # Para PDF, retornar HTML como fallback
                return exportar_html_simples(dados_filtrados, componente)
            else:
                return exportar_html_simples(dados_filtrados, componente)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao exportar dados financeiros: {e}")

        # Retornar página de erro como último recurso
        response = HttpResponse(
            f"""
            <html>
            <head><title>Erro de Exportação</title></head>
            <body>
                <h1>Erro ao exportar dados</h1>
                <p>Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde.</p>
                <p>Detalhe: {str(e)}</p>
                <a href="javascript:history.back()">Voltar</a>
            </body>
            </html>
            """,
            content_type="text/html",
        )
        return response


def exportar_csv(dados, componente):
    """Exportar dados para CSV"""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="financeiro_{componente}.csv"'
    )

    writer = csv.writer(response)

    if componente == "resumo":
        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Orçamento Total", f'R$ {dados["orcamento_total"]}'])
        writer.writerow(["Executado Total", f'R$ {dados["executado_total"]}'])
        writer.writerow(["Variação Período", f'{dados["variacao_periodo"]}%'])
    elif componente == "distribuicao":
        writer.writerow(["Unidade", "Orçamento", "Executado", "Percentual", "Status"])
        for unidade in dados["unidades"]:
            writer.writerow(
                [
                    unidade["nome"],
                    f'R$ {unidade["orcamento"]}',
                    f'R$ {unidade["executado"]}',
                    f'{unidade["percentual"]}%',
                    unidade["status"],
                ]
            )
    elif componente == "execucao":
        writer.writerow(["Mês", "Orçado", "Executado"])
        for execucao in dados["execucao_mensal"]:
            writer.writerow(
                [
                    execucao["mes"],
                    f'R$ {execucao["orcado"]}',
                    f'R$ {execucao["executado"]}',
                ]
            )
    else:  # completo
        # Sumário
        writer.writerow(["RELATÓRIO FINANCEIRO COMPLETO"])
        writer.writerow(["Período", dados["periodo"]])
        writer.writerow(["Data Geração", timezone.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([])

        # Resumo
        writer.writerow(["RESUMO FINANCEIRO"])
        writer.writerow(["Orçamento Total", f'R$ {dados["orcamento_total"]}'])
        writer.writerow(["Executado Total", f'R$ {dados["executado_total"]}'])
        writer.writerow(["Variação Período", f'{dados["variacao_periodo"]}%'])
        writer.writerow([])

        # Distribuição
        writer.writerow(["DISTRIBUIÇÃO POR UNIDADE"])
        writer.writerow(["Unidade", "Orçamento", "Executado", "Percentual", "Status"])
        for unidade in dados["unidades"]:
            writer.writerow(
                [
                    unidade["nome"],
                    f'R$ {unidade["orcamento"]}',
                    f'R$ {unidade["executado"]}',
                    f'{unidade["percentual"]}%',
                    unidade["status"],
                ]
            )
        writer.writerow([])

        # Execução
        writer.writerow(["EXECUÇÃO ORÇAMENTÁRIA"])
        writer.writerow(["Mês", "Orçado", "Executado"])
        for execucao in dados["execucao_mensal"]:
            writer.writerow(
                [
                    execucao["mes"],
                    f'R$ {execucao["orcado"]}',
                    f'R$ {execucao["executado"]}',
                ]
            )

    return response


def exportar_xlsx(dados, componente):
    """Exportar dados para XLSX"""
    try:
        import xlsxwriter
    except ImportError:
        # Fallback para CSV se xlsxwriter não estiver disponível
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="erro.txt"'
        response.write(
            "Biblioteca xlsxwriter não está instalada. Tente exportar como CSV."
        )
        return response

    # Criar arquivo temporário
    output = io.BytesIO()

    try:
        workbook = xlsxwriter.Workbook(output)

        # Formatos
        titulo_format = workbook.add_format(
            {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
        )
        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#D0D0D0", "border": 1}
        )
        cell_format = workbook.add_format({"border": 1})
        money_format = workbook.add_format({"num_format": "R$ #,##0.00", "border": 1})
        percent_format = workbook.add_format({"num_format": "0.0%", "border": 1})

        # Criar planilha baseada no componente
        if componente == "resumo":
            worksheet = workbook.add_worksheet("Resumo Financeiro")
            worksheet.set_column("A:A", 20)
            worksheet.set_column("B:B", 15)

            # Título
            worksheet.merge_range(
                "A1:B1", f'Resumo Financeiro - {dados["periodo"]}', titulo_format
            )

            # Cabeçalhos
            worksheet.write("A3", "Métrica", header_format)
            worksheet.write("B3", "Valor", header_format)

            # Dados
            row = 3
            worksheet.write(row, 0, "Orçamento Total", cell_format)
            worksheet.write(row, 1, float(dados["orcamento_total"]), money_format)
            row += 1
            worksheet.write(row, 0, "Executado Total", cell_format)
            worksheet.write(row, 1, float(dados["executado_total"]), money_format)
            row += 1
            worksheet.write(row, 0, "Variação Período", cell_format)
            worksheet.write(
                row, 1, float(dados["variacao_periodo"]) / 100, percent_format
            )

        elif componente == "distribuicao":
            worksheet = workbook.add_worksheet("Distribuição por Unidade")
            worksheet.set_column("A:A", 30)
            worksheet.set_column("B:D", 15)
            worksheet.set_column("E:E", 12)

            # Título
            worksheet.merge_range(
                "A1:E1", f'Distribuição por Unidade - {dados["periodo"]}', titulo_format
            )

            # Cabeçalhos
            worksheet.write("A3", "Unidade", header_format)
            worksheet.write("B3", "Orçamento", header_format)
            worksheet.write("C3", "Executado", header_format)
            worksheet.write("D3", "Percentual", header_format)
            worksheet.write("E3", "Status", header_format)

            # Dados
            row = 3
            for unidade in dados["unidades"]:
                worksheet.write(row, 0, unidade["nome"], cell_format)
                worksheet.write(row, 1, float(unidade["orcamento"]), money_format)
                worksheet.write(row, 2, float(unidade["executado"]), money_format)
                worksheet.write(
                    row, 3, float(unidade["percentual"]) / 100, percent_format
                )
                worksheet.write(row, 4, unidade["status"], cell_format)
                row += 1

        elif componente == "execucao":
            worksheet = workbook.add_worksheet("Execução Orçamentária")
            worksheet.set_column("A:A", 10)
            worksheet.set_column("B:C", 18)

            # Título
            worksheet.merge_range(
                "A1:C1", f'Execução Orçamentária - {dados["periodo"]}', titulo_format
            )

            # Cabeçalhos
            worksheet.write("A3", "Mês", header_format)
            worksheet.write("B3", "Orçado", header_format)
            worksheet.write("C3", "Executado", header_format)

            # Dados
            row = 3
            for execucao in dados["execucao_mensal"]:
                worksheet.write(row, 0, execucao["mes"], cell_format)
                worksheet.write(row, 1, float(execucao["orcado"]), money_format)
                worksheet.write(row, 2, float(execucao["executado"]), money_format)
                row += 1

        else:  # completo
            # Planilha de Resumo
            worksheet = workbook.add_worksheet("Resumo")
            worksheet.set_column("A:A", 20)
            worksheet.set_column("B:B", 15)

            # Título e informações
            worksheet.merge_range(
                "A1:B1", f'Relatório Financeiro - {dados["periodo"]}', titulo_format
            )
            worksheet.write("A2", "Data Geração:", cell_format)
            worksheet.write(
                "B2", timezone.now().strftime("%d/%m/%Y %H:%M"), cell_format
            )

            # Resumo
            worksheet.write("A4", "Métrica", header_format)
            worksheet.write("B4", "Valor", header_format)

            row = 4
            worksheet.write(row, 0, "Orçamento Total", cell_format)
            worksheet.write(row, 1, float(dados["orcamento_total"]), money_format)
            row += 1
            worksheet.write(row, 0, "Executado Total", cell_format)
            worksheet.write(row, 1, float(dados["executado_total"]), money_format)
            row += 1
            worksheet.write(row, 0, "Variação Período", cell_format)
            worksheet.write(
                row, 1, float(dados["variacao_periodo"]) / 100, percent_format
            )

            # Planilha de Distribuição
            worksheet = workbook.add_worksheet("Distribuição")
            worksheet.set_column("A:A", 30)
            worksheet.set_column("B:D", 15)
            worksheet.set_column("E:E", 12)

            # Título
            worksheet.merge_range("A1:E1", "Distribuição por Unidade", titulo_format)

            # Cabeçalhos
            worksheet.write("A3", "Unidade", header_format)
            worksheet.write("B3", "Orçamento", header_format)
            worksheet.write("C3", "Executado", header_format)
            worksheet.write("D3", "Percentual", header_format)
            worksheet.write("E3", "Status", header_format)

            # Dados
            row = 3
            for unidade in dados["unidades"]:
                worksheet.write(row, 0, unidade["nome"], cell_format)
                worksheet.write(row, 1, float(unidade["orcamento"]), money_format)
                worksheet.write(row, 2, float(unidade["executado"]), money_format)
                worksheet.write(
                    row, 3, float(unidade["percentual"]) / 100, percent_format
                )
                worksheet.write(row, 4, unidade["status"], cell_format)
                row += 1

            # Planilha de Execução
            worksheet = workbook.add_worksheet("Execução")
            worksheet.set_column("A:A", 10)
            worksheet.set_column("B:C", 18)

            # Título
            worksheet.merge_range("A1:C1", "Execução Orçamentária", titulo_format)

            # Cabeçalhos
            worksheet.write("A3", "Mês", header_format)
            worksheet.write("B3", "Orçado", header_format)
            worksheet.write("C3", "Executado", header_format)

            # Dados
            row = 3
            for execucao in dados["execucao_mensal"]:
                worksheet.write(row, 0, execucao["mes"], cell_format)
                worksheet.write(row, 1, float(execucao["orcado"]), money_format)
                worksheet.write(row, 2, float(execucao["executado"]), money_format)
                row += 1

        # Fechar o workbook
        workbook.close()

        # Preparar a resposta
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="financeiro_{componente}.xlsx"'
        )

        return response
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao criar arquivo Excel: {e}")

        # Retornar mensagem de erro se algo falhar
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="erro.txt"'
        response.write(f"Erro ao gerar arquivo Excel: {str(e)}")
        return response


def exportar_pdf(dados, componente):
    """Exportar dados para PDF"""
    try:
        # Se weasyprint estiver instalado, usamos para conversão HTML -> PDF
        from weasyprint import HTML

        try:
            # Primeiro geramos o HTML
            html_content = exportar_html(
                dados, componente, para_pdf=True
            ).content.decode("utf-8")

            # Converter HTML para PDF
            pdf_bytes = HTML(string=html_content).write_pdf()

            # Retornar como resposta
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="financeiro_{componente}.pdf"'
            )
            return response
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao gerar PDF: {e}")

            # Retornar mensagem de erro se algo falhar no processamento
            response = HttpResponse(content_type="text/plain")
            response["Content-Disposition"] = f'attachment; filename="erro_pdf.txt"'
            response.write(
                f"Erro ao gerar PDF: {str(e)}. Tente exportar como HTML ou CSV."
            )
            return response
    except ImportError:
        # Fallback: explicar que weasyprint não está instalado
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="erro.txt"'
        response.write(
            "Biblioteca weasyprint não está instalada. Tente exportar como HTML ou CSV."
        )
        return response


def exportar_html(dados, componente, para_pdf=False):
    """Exportar dados para HTML"""
    context = {
        "dados": dados,
        "componente": componente,
        "data_geracao": timezone.now(),
        "para_pdf": para_pdf,
    }

    # Renderizar o template HTML
    html_string = render_to_string("core/exports/financeira_export.html", context)

    response = HttpResponse(html_string, content_type="text/html")
    if not para_pdf:
        response["Content-Disposition"] = (
            f'inline; filename="financeiro_{componente}.html"'
        )

    return response


# Social login handling
class CustomSocialLoginView(SocialSignupView):
    """
    Handle social login success or failure
    """

    def get_success_url(self):
        return reverse_lazy("home")

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Falha na autenticação social. Por favor, tente novamente ou use outro método.",
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        # Additional logic for successful login can be added here
        return super().form_valid(form)

    # Sobrescrevendo para evitar loops de redirecionamento
    def get(self, request, *args, **kwargs):
        # Se o usuário já estiver autenticado, redirecione para a página inicial
        if request.user.is_authenticated:
            return redirect(self.get_success_url())

        # Processa os dados de sociallogin na sessão para criar um usuário
        sociallogin = request.session.get("socialaccount_sociallogin")
        if sociallogin:
            # Automaticamente cria o usuário e faz login
            user = sociallogin["user"]
            user.username = user.email.split("@")[0]  # Usa parte do email como username
            user.save()

            # Limpa a sessão e redireciona para home
            del request.session["socialaccount_sociallogin"]
            request.session.modified = True

            # Faz login manual do usuário
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect(self.get_success_url())

        return super().get(request, *args, **kwargs)


def simular_troca_cargo(request):
    if request.method == "POST":
        data = json.loads(request.body)
        unidade_id = data.get("unidade_id")
        cargo_atual = data.get("cargo_atual")
        cargo_novo = data.get("cargo_novo")

        # Buscar valores dos cargos
        cargo_atual_siorg = CargoSIORG.objects.filter(
            cargo=f"{cargo_atual['tipo']} {cargo_atual['categoria']} {cargo_atual['nivel']:02d}"
        ).first()

        cargo_novo_siorg = CargoSIORG.objects.filter(
            cargo=f"{cargo_novo['tipo']} {cargo_novo['categoria']} {cargo_novo['nivel']:02d}"
        ).first()

        if not cargo_atual_siorg or not cargo_novo_siorg:
            return JsonResponse({"error": "Cargo não encontrado"}, status=400)

        # Calcular diferenças
        diferenca_valor = (
            cargo_novo_siorg.unitario - cargo_atual_siorg.unitario
        ) * cargo_atual["quantidade"]
        diferenca_pontos = (
            cargo_novo_siorg.valor - cargo_atual_siorg.valor
        ) * cargo_atual["quantidade"]

        return JsonResponse(
            {
                "diferenca_valor": str(diferenca_valor),
                "diferenca_pontos": str(diferenca_pontos),
                "valor_atual": str(cargo_atual_siorg.valor * cargo_atual["quantidade"]),
                "valor_novo": str(cargo_novo_siorg.valor * cargo_atual["quantidade"]),
                "pontos_atual": str(
                    cargo_atual_siorg.unitario * cargo_atual["quantidade"]
                ),
                "pontos_novo": str(
                    cargo_novo_siorg.unitario * cargo_atual["quantidade"]
                ),
            }
        )

    return JsonResponse({"error": "Método não permitido"}, status=405)


@require_http_methods(["GET"])
def api_organograma(request):
    """API endpoint para fornecer os dados do organograma diretamente do banco de dados"""
    try:
        # Buscar todas as unidades com seus cargos
        unidades = (
            UnidadeCargo.objects.select_related("unidade")
            .exclude(grafo__exact="")
            .exclude(grafo__isnull=True)
        )

        # Primeiro passo: agrupar unidades por grafo completo
        unidades_por_grafo = {}
        for unidade in unidades:
            if unidade.grafo not in unidades_por_grafo:
                unidades_por_grafo[unidade.grafo] = []
            unidades_por_grafo[unidade.grafo].append(unidade)

        # Dicionário para armazenar dados processados das unidades
        unidades_dict = {}
        hierarquia = {}
        raizes = []

        # Processar cada grupo de unidades por grafo
        for grafo, grupo_unidades in unidades_por_grafo.items():
            # Ordenar unidades pelo nível do cargo (decrescente)
            grupo_unidades.sort(key=lambda x: x.nivel, reverse=True)

            # Usar a unidade com o cargo de maior nível como principal
            unidade_principal = grupo_unidades[0]
            niveis_grafo = grafo.split("-")
            codigo_unidade = niveis_grafo[-1]
            codigo_superior = niveis_grafo[-2] if len(niveis_grafo) > 1 else None

            # Calcular valores totais para todos os cargos do grupo
            valor_total = Decimal("0")
            pontos_total = Decimal("0")
            cargos_info = []

            for unidade in grupo_unidades:
                try:
                    cargo_siorg = CargoSIORG.objects.get(
                        cargo=f"{unidade.tipo_cargo} {unidade.categoria} {unidade.nivel:02d}"
                    )
                    valor = Decimal(
                        cargo_siorg.valor.replace("R$ ", "")
                        .replace(".", "")
                        .replace(",", ".")
                    )
                    pontos = cargo_siorg.unitario

                    cargo_info = {
                        "tipo": unidade.tipo_cargo,
                        "categoria": unidade.categoria,
                        "nivel": unidade.nivel,
                        "quantidade": unidade.quantidade,
                        "valor_unitario": float(valor),
                        "pontos_unitario": float(pontos),
                    }

                    valor_total += valor * unidade.quantidade
                    pontos_total += pontos * unidade.quantidade
                    cargos_info.append(cargo_info)
                except CargoSIORG.DoesNotExist:
                    print(
                        f"Cargo não encontrado: {unidade.tipo_cargo} {unidade.categoria} {unidade.nivel:02d}"
                    )

            # Armazenar dados da unidade usando a unidade principal (cargo de maior nível)
            dados_unidade = {
                "id": unidade_principal.id,
                "codigo": codigo_unidade,
                "nome": unidade_principal.unidade.denominacao,
                "sigla": unidade_principal.unidade.sigla,
                "tipo_cargo": unidade_principal.tipo_cargo,
                "nivel": unidade_principal.nivel,
                "cargos": sorted(cargos_info, key=lambda x: x["nivel"], reverse=True),
                "valores": {
                    "valor_total": float(valor_total),
                    "pontos_total": float(pontos_total),
                },
                "children": [],
            }

            unidades_dict[grafo] = dados_unidade

            # Registrar relação hierárquica usando o grafo completo
            if codigo_superior:
                grafo_pai = "-".join(niveis_grafo[:-1])
                if grafo_pai not in hierarquia:
                    hierarquia[grafo_pai] = []
                hierarquia[grafo_pai].append(grafo)
            else:
                raizes.append(grafo)

        # Construir a árvore hierárquica
        def construir_arvore(grafo):
            unidade = unidades_dict[grafo].copy()

            # Adicionar filhos
            if grafo in hierarquia:
                filhos = []
                for grafo_filho in hierarquia[grafo]:
                    filho = construir_arvore(grafo_filho)
                    filhos.append(filho)

                # Ordenar filhos pelo nível do cargo (decrescente)
                filhos.sort(key=lambda x: x["nivel"], reverse=True)
                unidade["children"] = filhos

                # Acumular valores
                for filho in filhos:
                    unidade["valores"]["valor_total"] += filho["valores"]["valor_total"]
                    unidade["valores"]["pontos_total"] += filho["valores"][
                        "pontos_total"
                    ]

            return unidade

        # Construir a árvore completa a partir das raízes
        arvore = []
        for grafo_raiz in raizes:
            arvore.append(construir_arvore(grafo_raiz))

        # Ordenar raízes pelo nível do cargo (decrescente)
        arvore.sort(key=lambda x: x["nivel"], reverse=True)

        return JsonResponse({"success": True, "data": arvore})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
