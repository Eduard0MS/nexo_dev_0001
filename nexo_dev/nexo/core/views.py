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
    CustomPasswordChangeForm
)
from .models import UnidadeCargo, CargoSIORG
from .utils import processa_planilhas, processa_organograma, estrutura_json_organograma, processa_json_organograma, gerar_anexo_simulacao
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
from .financeira_export import dados_financeiros_backup, exportar_csv_simples, exportar_html_simples
import random
from datetime import datetime
from .models import Perfil
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods
from decimal import Decimal
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .dados_json_update import gerar_organograma_json
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views import View
from .models import SimulacaoSalva


class CustomLoginView(LoginView):
    template_name = "registration/login_direct.html"
    authentication_form = CustomLoginForm
    success_url = reverse_lazy("home")
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy("home")

    def form_invalid(self, form):
        # Implementar rate limiting apenas em produção
        if not settings.DEBUG:
            ip = self.request.META.get('REMOTE_ADDR')
            cache_key = f'login_attempts_{ip}'
            attempts = cache.get(cache_key, 0)
            
            if attempts >= 5:
                return HttpResponseForbidden("Muitas tentativas de login. Tente novamente em 15 minutos.")
            
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
    # Redirecionar para a página de login com mensagem informativa
    messages.info(request, "O cadastro de usuários só pode ser feito pelo administrador do sistema.")
    return redirect("login")


@login_required(login_url="/login_direct/")
def home(request, form=None):
    return render(request, "home.html", {"form": form})


@login_required
def organograma(request):
    """Renderiza a página do organograma."""
    
    try:
        from .utils import estrutura_json_organograma
        from .models import UnidadeCargo, CargoSIORG
        import json
        
        # Buscar dados diretamente do banco de dados
        dados = estrutura_json_organograma()
        
        # Converter para string JSON para passar ao template
        organograma_data_json = json.dumps({
            'core_unidadecargo': dados,
            'core_cargosiorg': [
                {
                    'cargo': f"{cargo.cargo}",
                    'valor': str(cargo.valor),
                    'unitario': float(cargo.unitario)
                }
                for cargo in CargoSIORG.objects.all()
            ]
        })
        
    except Exception as e:
        # Log do erro e usar dados mínimos como fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao carregar dados do organograma: {str(e)}")
        
        organograma_data_json = json.dumps({
            "core_unidadecargo": [
                {
                    "tipo_unidade": "Órgão",
                    "denominacao_unidade": "Ministério do Planejamento e Orçamento - MPO",
                    "codigo_unidade": "308804",
                    "sigla": "MPO",
                    "tipo_cargo": "MEST",
                    "denominacao": "Ministro de Estado",
                    "categoria": 0,
                    "nivel": 0,
                    "quantidade": 1,
                    "grafo": "308804"
                }
            ],
            "core_cargosiorg": []
        })
    
    return render(request, 'core/organograma.html', {
        'organograma_data': organograma_data_json
    })
    

@login_required
def organograma_view(request):
    return render(request, 'core/organograma.html')


@require_http_methods(["GET"])
def organograma_redirect(request):
    """View para redirecionar da URL original do organograma para a nova visualização"""
    return render(request, 'organograma_redirect.html')


@login_required
def organograma_data(request):
    """
    Endpoint que retorna os dados do organograma em formato JSON.
    """
    from .utils import processa_organograma
    from .models import UnidadeCargo
    
    try:
        # Buscar dados do organograma
        organograma = processa_organograma()
        
        # Contar total de unidades
        total_unidades = len(organograma)
        
        # Contar unidades com valores
        unidades_com_valores = sum(1 for info in organograma.values() if info.get('custo_total', 0) > 0)
        
        # Preparar mensagem sobre os dados filtrados
        mensagem = ""
        if total_unidades > 0:
            total_registros = UnidadeCargo.objects.count()
            registros_filtrados = total_registros - UnidadeCargo.objects.exclude(grafo__exact='').exclude(grafo__isnull=True).count()
            
            if registros_filtrados > 0:
                mensagem = f"{registros_filtrados} registros foram filtrados por não pertencerem à estrutura do ministério."
        
        # Retornar os dados em formato JSON
        return JsonResponse({
            'status': 'success',
            'data': organograma,
            'meta': {
                'total_unidades': total_unidades,
                'unidades_com_valores': unidades_com_valores,
                'mensagem': mensagem
            }
        })
    except Exception as e:
        # Log do erro para depuração
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao processar dados do organograma: {str(e)}")
        
        # Retornar mensagem de erro
        return JsonResponse({
            'status': 'error',
            'message': f'Ocorreu um erro ao processar os dados: {str(e)}'
        }, status=500)


@login_required
def organograma_page(request):
    """Renderiza a página do organograma."""
    return render(request, 'core/organograma.html')


@login_required(login_url="/login_direct/")
def simulacao_page(request):
    """
    View que renderiza a página de simulação do organograma
    onde o usuário pode adicionar nomes e criar conexões manualmente.
    """
    from django.http import JsonResponse
    import json
    
    try:
        # Tentar ler o arquivo organograma.json para passar ao template
        import os
        from django.conf import settings
        
        json_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'data', 'organograma.json')
        
        # Verificar se o arquivo existe
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                organograma_data = json.load(f)
                
            # Converter para string JSON para passar ao template
            organograma_data_json = json.dumps(organograma_data)
        else:
            # Se o arquivo não existir, usar um objeto vazio
            organograma_data_json = json.dumps({
                "core_unidadecargo": []
            })
    except Exception as e:
        # Em caso de erro, usar um objeto vazio
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao carregar dados do organograma para simulacao_page: {str(e)}")
        
        organograma_data_json = json.dumps({
            "core_unidadecargo": []
        })
    
    return render(request, "core/simulacao.html", {
        'organograma_data': organograma_data_json
    })


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
    Retorna dados financeiros em formato JSON reutilizando a mesma
    lógica empregada pela API de Organograma. Toda a computação é
    delegada à função `financeira_data_real`, garantindo consistência
    e eliminando a antiga API simulada.
    """

    # Delega imediatamente para a implementação baseada no organograma.
    return financeira_data_real(request)


@login_required(login_url="/login_direct/")
def financeira_export(request):
    """
    Exporta dados financeiros em diferentes formatos: PDF, CSV, XLSX, HTML
    """
    try:
        # Processar parâmetros do request
        formato = request.GET.get('formato', 'html')
        periodo = request.GET.get('periodo', 'Mês Atual')
        componente = request.GET.get('componente', 'completo')
        
        # Obter dados financeiros
        # Reutilização da lógica de financeira_data
        try:
            response = financeira_data(request)
            if response.status_code == 200:
                dados = json.loads(response.content)
                dados["titulo"] = "Relatório de Pontuação"
                dados["periodo"] = periodo
            else:
                # Usar dados de backup
                dados = dados_financeiros_backup()
        except Exception:
            # Em caso de erro, usar dados de backup
            dados = dados_financeiros_backup()
            
        # Filtrar dados conforme o componente solicitado
        if componente == 'resumo':
            dados_filtrados = {
                "orcamento_total": dados["orcamento_total"],
                "executado_total": dados["executado_total"],
                "variacao_periodo": dados["variacao_periodo"],
                "titulo": "Resumo de Pontuação",
                "periodo": periodo
            }
        elif componente == 'distribuicao':
            dados_filtrados = {
                "unidades": dados["unidades"],
                "titulo": "Distribuição por Unidade",
                "periodo": periodo
            }
        elif componente == 'execucao':
            dados_filtrados = {
                "execucao_mensal": dados["execucao_mensal"],
                "titulo": "Execução Orçamentária",
                "periodo": periodo
            }
        else:  # completo
            dados_filtrados = dados
            
        # Exportar conforme o formato
        try:
            if formato == 'csv':
                return exportar_csv(dados_filtrados, componente)
            elif formato == 'xlsx':
                return exportar_xlsx(dados_filtrados, componente)
            elif formato == 'pdf':
                return exportar_pdf(dados_filtrados, componente)
            else:  # html
                return exportar_html(dados_filtrados, componente)
        except Exception as e:
            # Em caso de falha na exportação, usar versões simplificadas de backup
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao exportar dados no formato {formato}: {e}")
            
            if formato == 'csv':
                return exportar_csv_simples(dados_filtrados, componente)
            elif formato == 'xlsx':
                # Para XLSX, retornar CSV como fallback
                return exportar_csv_simples(dados_filtrados, componente)
            elif formato == 'pdf':
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
            content_type='text/html'
        )
        return response


def exportar_csv(dados, componente):
    """Exportar dados para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="financeiro_{componente}.csv"'
    
    writer = csv.writer(response)
    
    if componente == 'resumo':
        writer.writerow(['Métrica', 'Valor'])
        writer.writerow(['Orçamento Total', f'R$ {dados["orcamento_total"]}'])
        writer.writerow(['Executado Total', f'R$ {dados["executado_total"]}'])
        writer.writerow(['Variação Período', f'{dados["variacao_periodo"]}%'])
    elif componente == 'distribuicao':
        writer.writerow(['Unidade', 'Orçamento', 'Executado', 'Percentual', 'Status'])
        for unidade in dados["unidades"]:
            writer.writerow([
                unidade["nome"],
                f'R$ {unidade["orcamento"]}',
                f'R$ {unidade["executado"]}',
                f'{unidade["percentual"]}%',
                unidade["status"]
            ])
    elif componente == 'execucao':
        writer.writerow(['Mês', 'Orçado', 'Executado'])
        for execucao in dados["execucao_mensal"]:
            writer.writerow([
                execucao["mes"],
                f'R$ {execucao["orcado"]}',
                f'R$ {execucao["executado"]}'
            ])
    else:  # completo
        # Sumário
        writer.writerow(['RELATÓRIO FINANCEIRO COMPLETO'])
        writer.writerow(['Período', dados["periodo"]])
        writer.writerow(['Data Geração', timezone.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Resumo
        writer.writerow(['RESUMO FINANCEIRO'])
        writer.writerow(['Orçamento Total', f'R$ {dados["orcamento_total"]}'])
        writer.writerow(['Executado Total', f'R$ {dados["executado_total"]}'])
        writer.writerow(['Variação Período', f'{dados["variacao_periodo"]}%'])
        writer.writerow([])
        
        # Distribuição
        writer.writerow(['DISTRIBUIÇÃO POR UNIDADE'])
        writer.writerow(['Unidade', 'Orçamento', 'Executado', 'Percentual', 'Status'])
        for unidade in dados["unidades"]:
            writer.writerow([
                unidade["nome"],
                f'R$ {unidade["orcamento"]}',
                f'R$ {unidade["executado"]}',
                f'{unidade["percentual"]}%',
                unidade["status"]
            ])
        writer.writerow([])
        
        # Execução
        writer.writerow(['EXECUÇÃO ORÇAMENTÁRIA'])
        writer.writerow(['Mês', 'Orçado', 'Executado'])
        for execucao in dados["execucao_mensal"]:
            writer.writerow([
                execucao["mes"],
                f'R$ {execucao["orcado"]}',
                f'R$ {execucao["executado"]}'
            ])
            
    return response


def exportar_xlsx(dados, componente):
    """Exportar dados para XLSX"""
    try:
        import xlsxwriter
    except ImportError:
        # Fallback para CSV se xlsxwriter não estiver disponível
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="erro.txt"'
        response.write('Biblioteca xlsxwriter não está instalada. Tente exportar como CSV.')
        return response
    
    # Criar arquivo temporário
    output = io.BytesIO()
    
    try:
        workbook = xlsxwriter.Workbook(output)
        
        # Formatos
        titulo_format = workbook.add_format({
            'bold': True, 
            'font_size': 14, 
            'align': 'center', 
            'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#D0D0D0', 
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({
            'num_format': 'R$ #,##0.00',
            'border': 1
        })
        percent_format = workbook.add_format({
            'num_format': '0.0%',
            'border': 1
        })
        
        # Criar planilha baseada no componente
        if componente == 'resumo':
            worksheet = workbook.add_worksheet('Resumo Financeiro')
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 15)
            
            # Título
            worksheet.merge_range('A1:B1', f'Resumo Financeiro - {dados["periodo"]}', titulo_format)
            
            # Cabeçalhos
            worksheet.write('A3', 'Métrica', header_format)
            worksheet.write('B3', 'Valor', header_format)
            
            # Dados
            row = 3
            worksheet.write(row, 0, 'Orçamento Total', cell_format)
            worksheet.write(row, 1, float(dados["orcamento_total"]), money_format)
            row += 1
            worksheet.write(row, 0, 'Executado Total', cell_format)
            worksheet.write(row, 1, float(dados["executado_total"]), money_format)
            row += 1
            worksheet.write(row, 0, 'Variação Período', cell_format)
            worksheet.write(row, 1, float(dados["variacao_periodo"]) / 100, percent_format)
            
        elif componente == 'distribuicao':
            worksheet = workbook.add_worksheet('Distribuição por Unidade')
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:D', 15)
            worksheet.set_column('E:E', 12)
            
            # Título
            worksheet.merge_range('A1:E1', f'Distribuição por Unidade - {dados["periodo"]}', titulo_format)
            
            # Cabeçalhos
            worksheet.write('A3', 'Unidade', header_format)
            worksheet.write('B3', 'Orçamento', header_format)
            worksheet.write('C3', 'Executado', header_format)
            worksheet.write('D3', 'Percentual', header_format)
            worksheet.write('E3', 'Status', header_format)
            
            # Dados
            row = 3
            for unidade in dados["unidades"]:
                worksheet.write(row, 0, unidade["nome"], cell_format)
                worksheet.write(row, 1, float(unidade["orcamento"]), money_format)
                worksheet.write(row, 2, float(unidade["executado"]), money_format)
                worksheet.write(row, 3, float(unidade["percentual"]) / 100, percent_format)
                worksheet.write(row, 4, unidade["status"], cell_format)
                row += 1
                
        elif componente == 'execucao':
            worksheet = workbook.add_worksheet('Execução Orçamentária')
            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:C', 18)
            
            # Título
            worksheet.merge_range('A1:C1', f'Execução Orçamentária - {dados["periodo"]}', titulo_format)
            
            # Cabeçalhos
            worksheet.write('A3', 'Mês', header_format)
            worksheet.write('B3', 'Orçado', header_format)
            worksheet.write('C3', 'Executado', header_format)
            
            # Dados
            row = 3
            for execucao in dados["execucao_mensal"]:
                worksheet.write(row, 0, execucao["mes"], cell_format)
                worksheet.write(row, 1, float(execucao["orcado"]), money_format)
                worksheet.write(row, 2, float(execucao["executado"]), money_format)
                row += 1
                
        else:  # completo
            # Planilha de Resumo
            worksheet = workbook.add_worksheet('Resumo')
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 15)
            
            # Título e informações
            worksheet.merge_range('A1:B1', f'Relatório Financeiro - {dados["periodo"]}', titulo_format)
            worksheet.write('A2', 'Data Geração:', cell_format)
            worksheet.write('B2', timezone.now().strftime('%d/%m/%Y %H:%M'), cell_format)
            
            # Resumo
            worksheet.write('A4', 'Métrica', header_format)
            worksheet.write('B4', 'Valor', header_format)
            
            row = 4
            worksheet.write(row, 0, 'Orçamento Total', cell_format)
            worksheet.write(row, 1, float(dados["orcamento_total"]), money_format)
            row += 1
            worksheet.write(row, 0, 'Executado Total', cell_format)
            worksheet.write(row, 1, float(dados["executado_total"]), money_format)
            row += 1
            worksheet.write(row, 0, 'Variação Período', cell_format)
            worksheet.write(row, 1, float(dados["variacao_periodo"]) / 100, percent_format)
            
            # Planilha de Distribuição
            worksheet = workbook.add_worksheet('Distribuição')
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:D', 15)
            worksheet.set_column('E:E', 12)
            
            # Título
            worksheet.merge_range('A1:E1', 'Distribuição por Unidade', titulo_format)
            
            # Cabeçalhos
            worksheet.write('A3', 'Unidade', header_format)
            worksheet.write('B3', 'Orçamento', header_format)
            worksheet.write('C3', 'Executado', header_format)
            worksheet.write('D3', 'Percentual', header_format)
            worksheet.write('E3', 'Status', header_format)
            
            # Dados
            row = 3
            for unidade in dados["unidades"]:
                worksheet.write(row, 0, unidade["nome"], cell_format)
                worksheet.write(row, 1, float(unidade["orcamento"]), money_format)
                worksheet.write(row, 2, float(unidade["executado"]), money_format)
                worksheet.write(row, 3, float(unidade["percentual"]) / 100, percent_format)
                worksheet.write(row, 4, unidade["status"], cell_format)
                row += 1
                
            # Planilha de Execução
            worksheet = workbook.add_worksheet('Execução')
            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:C', 18)
            
            # Título
            worksheet.merge_range('A1:C1', 'Execução Orçamentária', titulo_format)
            
            # Cabeçalhos
            worksheet.write('A3', 'Mês', header_format)
            worksheet.write('B3', 'Orçado', header_format)
            worksheet.write('C3', 'Executado', header_format)
            
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
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="financeiro_{componente}.xlsx"'
        
        return response
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao criar arquivo Excel: {e}")
        
        # Retornar mensagem de erro se algo falhar
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="erro.txt"'
        response.write(f'Erro ao gerar arquivo Excel: {str(e)}')
        return response


def exportar_pdf(dados, componente):
    """Exportar dados para PDF"""
    try:
        # Se weasyprint estiver instalado, usamos para conversão HTML -> PDF
        from weasyprint import HTML
        
        try:
            # Primeiro geramos o HTML
            html_content = exportar_html(dados, componente, para_pdf=True).content.decode('utf-8')
            
            # Converter HTML para PDF
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            # Retornar como resposta
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="financeiro_{componente}.pdf"'
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao gerar PDF: {e}")
            
            # Retornar mensagem de erro se algo falhar no processamento
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="erro_pdf.txt"'
            response.write(f'Erro ao gerar PDF: {str(e)}. Tente exportar como HTML ou CSV.')
            return response
    except ImportError:
        # Fallback: explicar que weasyprint não está instalado
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="erro.txt"'
        response.write('Biblioteca weasyprint não está instalada. Tente exportar como HTML ou CSV.')
        return response


def exportar_html(dados, componente, para_pdf=False):
    """Exportar dados para HTML"""
    context = {
        'dados': dados,
        'componente': componente,
        'data_geracao': timezone.now(),
        'para_pdf': para_pdf
    }
    
    # Renderizar o template HTML
    html_string = render_to_string('core/exports/financeira_export.html', context)
    
    response = HttpResponse(html_string, content_type='text/html')
    if not para_pdf:
        response['Content-Disposition'] = f'inline; filename="financeiro_{componente}.html"'
    
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
    if request.method == 'POST':
        data = json.loads(request.body)
        unidade_id = data.get('unidade_id')
        cargo_atual = data.get('cargo_atual')
        cargo_novo = data.get('cargo_novo')
        
        # Buscar valores dos cargos
        cargo_atual_siorg = CargoSIORG.objects.filter(
            cargo=f"{cargo_atual['tipo']} {cargo_atual['categoria']} {cargo_atual['nivel']:02d}"
        ).first()
        
        cargo_novo_siorg = CargoSIORG.objects.filter(
            cargo=f"{cargo_novo['tipo']} {cargo_novo['categoria']} {cargo_novo['nivel']:02d}"
        ).first()
        
        if not cargo_atual_siorg or not cargo_novo_siorg:
            return JsonResponse({'error': 'Cargo não encontrado'}, status=400)
        
        # Calcular diferenças
        diferenca_valor = (cargo_novo_siorg.unitario - cargo_atual_siorg.unitario) * cargo_atual['quantidade']
        diferenca_pontos = (cargo_novo_siorg.valor - cargo_atual_siorg.valor) * cargo_atual['quantidade']
        
        return JsonResponse({
            'diferenca_valor': str(diferenca_valor),
            'diferenca_pontos': str(diferenca_pontos),
            'valor_atual': str(cargo_atual_siorg.valor * cargo_atual['quantidade']),
            'valor_novo': str(cargo_novo_siorg.valor * cargo_atual['quantidade']),
            'pontos_atual': str(cargo_atual_siorg.unitario * cargo_atual['quantidade']),
            'pontos_novo': str(cargo_novo_siorg.unitario * cargo_atual['quantidade'])
        })
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)


@login_required
@require_http_methods(["GET"])
def view_organograma(request):
    """View para exibir o organograma visual com D3.js"""
    return render(request, 'organograma.html')


@require_http_methods(["GET"])
def api_organograma(request):
    """API endpoint para fornecer os dados do organograma diretamente do banco de dados"""
    try:
        # Usar o mesmo arquivo JSON que usamos para o template
        json_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'data', 'organograma.json')
        
        # Verificar se o arquivo existe
        if not os.path.exists(json_path):
            return JsonResponse({
                'error': 'Arquivo organograma.json não encontrado. Execute uma atualização no Admin primeiro.'
            }, status=404)
            
        # Carregar os dados
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Se dados é uma lista com um único item, extrair esse item
        if isinstance(dados, list) and len(dados) == 1:
            dados = dados[0]
            
        # Retornar os dados sem modificações adicionais
        return JsonResponse(dados, safe=True)
        
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar organograma.json: {str(e)}")
        return JsonResponse({
            'error': f'Erro ao decodificar o arquivo de dados: {str(e)}',
            'core_unidadecargo': []
        }, status=500)
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Erro em api_organograma: {str(e)}\n{traceback_str}")
        return JsonResponse({
            'error': f'Erro inesperado: {str(e)}',
            'stack_trace': traceback_str,
            'core_unidadecargo': []
        }, status=500)


@require_http_methods(["GET"])
def teste_api_organograma(request):
    """API endpoint para fornecer os dados do organograma diretamente do banco de dados (para teste)"""
    try:
        # Usar o dados.json para servir ao organograma
        dados_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dados.json')
        
        # Verificar se o arquivo existe
        if not os.path.exists(dados_json_path):
            return JsonResponse({
                'error': 'Arquivo dados.json não encontrado. Execute uma atualização no Admin primeiro.'
            }, status=404)
            
        # Carregar os dados
        with open(dados_json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Verificar formato dos dados
        dados_validos = False
        if isinstance(dados, dict) and "unidades" in dados:
            dados_validos = True
        elif isinstance(dados, list) and len(dados) > 0:
            dados_validos = True
            dados = dados[0] if len(dados) == 1 else dados
        
        # Para teste, adicionar informações extras
        dados_debug = dados if dados_validos else {'error': 'Formato de dados inválido ou vazio'}
        
        # Adicionar informações de debug
        if isinstance(dados_debug, dict):
            dados_debug['_debug_info'] = {
                'tipo': type(dados).__name__,
                'tamanho': len(str(dados)),
                'chaves': list(dados.keys() if isinstance(dados, dict) else []),
                'unidades_count': len(dados.get('unidades', []) if isinstance(dados, dict) else []),
                'path': dados_json_path,
                'valido': dados_validos
            }
        
        # Retornar os dados brutos para inspeção
        return HttpResponse(json.dumps(dados_debug, indent=2, ensure_ascii=False), 
                          content_type='application/json')
    
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': f'Erro ao decodificar o arquivo de dados: {str(e)}'
        }, status=500)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'error': f'Erro inesperado: {str(e)}'
        }, status=500)


@login_required
def perfil(request):
    """
    Exibe a página de perfil do usuário.
    """
    return render(request, 'core/perfil/perfil.html', {
        'perfil': request.user.perfil
    })

@login_required
def editar_perfil(request):
    """
    Permite ao usuário editar suas informações de perfil.
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)
        
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            
            # Se o usuário solicitou a remoção da foto
            if request.POST.get('delete_foto') == 'true' and request.user.perfil.foto:
                request.user.perfil.foto.delete()
                request.user.perfil.foto = None
                request.user.perfil.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
    else:
        user_form = UserUpdateForm(instance=request.user)
        perfil_form = PerfilUpdateForm(instance=request.user.perfil)
    
    return render(request, 'core/perfil/editar_perfil.html', {
        'user_form': user_form,
        'perfil_form': perfil_form
    })

@login_required
def alterar_senha(request):
    """
    Permite ao usuário alterar sua senha.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('perfil')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'core/perfil/alterar_senha.html', {
        'form': form
    })

def index(request):
    # Filtrar para mostrar apenas unidades com grafo válido
    unidades_validas = UnidadeCargo.objects.exclude(
        Q(grafo__exact='') | Q(grafo__isnull=True)
    )
    
    # Contar registros totais e filtrados
    total_registros = UnidadeCargo.objects.count()
    total_validos = unidades_validas.count()
    
    # Construir contexto
    context = {
        'title': 'Dashboard NEXO',
        'unidades': unidades_validas,
        'total_registros': total_registros,
        'total_validos': total_validos,
        'registros_filtrados': total_registros - total_validos
    }
    
    return render(request, 'core/index.html', context)

def get_unidade_data(request, codigo_unidade):
    try:
        # Garantir que só buscamos unidades com grafos válidos
        unidade = UnidadeCargo.objects.exclude(
            Q(grafo__exact='') | Q(grafo__isnull=True)
        ).get(codigo_unidade=codigo_unidade)
        
        # Converter o grafo de string JSON para objeto Python
        grafo_data = json.loads(unidade.grafo) if unidade.grafo else {}
        
        # Construir resposta
        data = {
            'success': True,
            'unidade': {
                'codigo': unidade.codigo_unidade,
                'denominacao': unidade.denominacao_unidade,
                'tipo_cargo': unidade.tipo_cargo,
                'categoria': unidade.categoria,
                'nivel': unidade.nivel,
                'grafo': grafo_data
            }
        }
    except UnidadeCargo.DoesNotExist:
        data = {
            'success': False,
            'error': 'Unidade não encontrada ou sem estrutura válida'
        }
    except json.JSONDecodeError:
        data = {
            'success': False,
            'error': 'Erro ao decodificar os dados do grafo'
        }
    
    return JsonResponse(data)

@api_view(['GET'])
def api_organograma_detalhes(request, codigo):
    """
    API para obter detalhes específicos de uma unidade pelo código.
    Esta API é usada para carregar detalhes sob demanda no organograma.
    """
    try:
        # Usar o dados.json para buscar detalhes da unidade
        dados_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dados.json')
        
        # Verificar se o arquivo existe
        if not os.path.exists(dados_json_path):
            return Response({
                'error': 'Arquivo dados.json não encontrado. Execute uma atualização no Admin primeiro.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Carregar o arquivo dados.json
        with open(dados_json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
        # Buscar a unidade específica pelo código
        unidade = None
        for u in dados.get('unidades', []):
            if u and str(u.get('codigo', '')) == str(codigo):
                unidade = u
                break
                
        if not unidade:
            return Response({
                'error': f'Unidade com código {codigo} não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Retornar os detalhes da unidade
        return Response(unidade)
        
    except Exception as e:
        return Response({
            'error': f'Erro ao buscar detalhes da unidade: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def organograma_ondemand(request):
    """
    Visualização do organograma com carregamento sob demanda.
    Esta versão carrega os dados de forma incremental para evitar
    travamentos no navegador.
    """
    return render(request, 'core/organograma_ondemand.html')

@csrf_exempt
def atualizar_organograma_json(request):
    """View para forçar atualização do arquivo organograma.json via AJAX"""
    if request.method == 'POST':
        try:
            gerar_organograma_json()
            return JsonResponse({'success': True, 'message': 'Arquivo organograma.json atualizado com sucesso.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao atualizar: {str(e)}'}, status=500)
    return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)

@require_http_methods(["GET"])
def api_organograma_filter(request):
    """API endpoint para filtrar dados do organograma de forma otimizada preservando estrutura hierárquica"""
    import json
    import os
    from django.conf import settings
    from django.http import JsonResponse
    from django.db.models import Q
    
    # Obter parâmetros de filtro
    sigla = request.GET.get('sigla', '').upper()
    cargo = request.GET.get('cargo', '')
    nivel = request.GET.get('nivel', '')
    
    # Caminho para o JSON original
    json_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'data', 'organograma.json')
    
    try:
        # Carregar dados do JSON
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            # Se não há filtros, retornar dados completos
            if not sigla and not cargo and not nivel:
                return JsonResponse(data)
            
            # Estes serão os códigos de unidades filtradas + todos os seus ancestrais e descendentes
            codigos_para_incluir = set()
            
            # Lista de todas as unidades
            units = data.get('core_unidadecargo', [])
            
            # Primeiro, identificar unidades que atendem aos critérios de filtro
            filtered_codes = []
            for unit in units:
                # Se passa pelos filtros
                if ((not sigla or (unit.get('sigla', '').upper().find(sigla) >= 0)) and
                    (not cargo or unit.get('tipo_cargo') == cargo) and
                    (not nivel or str(unit.get('nivel')) == nivel)):
                    filtered_codes.append(unit.get('codigo_unidade'))
                    codigos_para_incluir.add(unit.get('codigo_unidade'))
            
            # Para cada código filtrado, adicionar ancestrais e descendentes
            for unit in units:
                # Se esta unidade foi filtrada, adicionar ascendentes e descendentes
                if unit.get('codigo_unidade') in filtered_codes:
                    grafo = unit.get('grafo', '')
                    if grafo:
                        # Adicionar ancestrais (todos os segmentos do grafo são ancestrais)
                        ancestrais = grafo.split('-')
                        for ancestral in ancestrais:
                            codigos_para_incluir.add(ancestral)
                
                # Verificar se é descendente de alguma unidade filtrada
                grafo = unit.get('grafo', '')
                if grafo:
                    for filtered_code in filtered_codes:
                        # Se o grafo contém o código filtrado como um segmento, é descendente
                        segments = grafo.split('-')
                        if filtered_code in segments:
                            codigos_para_incluir.add(unit.get('codigo_unidade'))
                            break
            
            # Criar uma nova lista incluindo apenas unidades da hierarquia filtrada
            filtered_units = [unit for unit in units if unit.get('codigo_unidade') in codigos_para_incluir]
            
            # Substituir dados originais com dados filtrados
            result = {
                'core_unidadecargo': filtered_units,
                'core_cargosiorg': data.get('core_cargosiorg', [])
            }
            
            return JsonResponse(result)
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao filtrar dados do organograma: {str(e)}")
        
        # Retornar dados de fallback em caso de erro
        return JsonResponse({
            "core_unidadecargo": [
                {
                    "tipo_unidade": "Órgão",
                    "denominacao_unidade": "Ministério do Planejamento e Orçamento - MPO",
                    "codigo_unidade": "308804",
                    "sigla": "MPO",
                    "tipo_cargo": "MEST",
                    "denominacao": "Ministro de Estado",
                    "categoria": 0,
                    "nivel": 0,
                    "quantidade": 1,
                    "grafo": "308804"
                }
            ],
            "core_cargosiorg": []
        })

@require_http_methods(["GET"])
def api_cargos(request):
    """API endpoint para buscar dados de cargos de forma específica (para a tabela)"""
    import json
    import os
    from django.conf import settings
    from django.http import JsonResponse
    from .models import UnidadeCargo
    
    # Obter parâmetros de filtro
    sigla = request.GET.get('sigla', '').upper()
    tipo_cargo = request.GET.get('tipo_cargo', '')
    nivel = request.GET.get('nivel', '')
    
    try:
        # Construir a query base
        query = UnidadeCargo.objects.all()
        
        # Aplicar filtros
        if sigla:
            query = query.filter(sigla__icontains=sigla)
        
        if tipo_cargo:
            query = query.filter(tipo_cargo=tipo_cargo)
            
        if nivel:
            query = query.filter(nivel=nivel)
            
        # Executar a consulta
        cargos = query.select_related('unidade').order_by('-nivel')
        
        # Converter para o formato esperado pelo frontend
        result = []
        for cargo in cargos:
            # Calcular valores derivados
            pontos = float(cargo.pontos) if cargo.pontos else 0
            quantidade = int(cargo.quantidade) if cargo.quantidade else 0
            valor_unitario = float(cargo.valor_unitario) if cargo.valor_unitario else 0
            
            # Calcular pontos_total e gasto_total
            pontos_total = pontos * quantidade
            gasto_total = pontos * quantidade * valor_unitario
            
            result.append({
                'codigo_unidade': cargo.unidade.codigo if cargo.unidade else '',
                'sigla': cargo.sigla or '',
                'tipo_unidade': cargo.tipo_unidade or '',
                'denominacao_unidade': cargo.denominacao_unidade or '',
                'tipo_cargo': cargo.tipo_cargo or '',
                'denominacao': cargo.denominacao or '',
                'categoria': cargo.categoria,
                'nivel': cargo.nivel,
                'quantidade': quantidade,
                'pontos': pontos,
                'valor_unitario': valor_unitario,
                'pontos_total': pontos_total,
                'gasto_total': gasto_total,
                'grafo': cargo.grafo or ''
            })
            
        return JsonResponse({'dados': result})
        
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao buscar dados de cargos: {str(e)}")
        
        # Retornar dados de fallback em caso de erro
        return JsonResponse({
            'erro': f'Ocorreu um erro ao buscar os dados: {str(e)}',
            'dados': []
        }, status=500)

@login_required
def api_cargos_diretos(request):
    """API endpoint para buscar dados de cargos diretamente do banco de dados com paginação"""
    from django.http import JsonResponse
    from .models import UnidadeCargo, CargoSIORG
    from django.core.paginator import Paginator
    import decimal
    # Importações para construir query OR
    from functools import reduce
    import operator

    # Configurar logging
    import logging
    logger = logging.getLogger(__name__)
    
    # Obter parâmetros de filtro e paginação
    sigla = request.GET.get('sigla', '').upper()
    tipo_cargo = request.GET.get('tipo_cargo', '')
    nivel = request.GET.get('nivel', '')
    
    # Parâmetros de paginação
    pagina = int(request.GET.get('pagina', 1))
    tamanho = int(request.GET.get('tamanho', 20))
    
    logger.info(f"API cargos_diretos - Parâmetros: sigla={sigla}, tipo_cargo={tipo_cargo}, nivel={nivel}, pagina={pagina}, tamanho={tamanho}")
    
    try:
        # Consulta base
        query = UnidadeCargo.objects.all()
        logger.info(f"Total de registros na tabela UnidadeCargo: {query.count()}")
        
        # Se houver sigla, aplicar filtro especial
        if sigla:
            logger.info(f"Iniciando processamento de filtro por sigla: {sigla}")
            
            # Buscamos registros onde a sigla aparece diretamente (nos campos indicados)
            codigos_associados = UnidadeCargo.objects.filter(
                Q(sigla_unidade__icontains=sigla) | 
                Q(sigla__icontains=sigla) |
                Q(denominacao_unidade__icontains=sigla)
            ).values_list('codigo_unidade', flat=True).distinct()
            
            codigos_lista = list(codigos_associados)
            logger.info(f"Códigos de unidade associados à sigla '{sigla}': {codigos_lista[:10]} (total: {len(codigos_lista)})")
            
            if codigos_lista:
                # Em vez de usar somente a união dos códigos, usamos um filtro OR:
                query = query.filter(
                    Q(codigo_unidade__in=codigos_lista) |
                    reduce(operator.or_, (Q(grafo__icontains=code) for code in codigos_lista))
                )
                logger.info(f"Filtrando registros com código ou grafo contendo os códigos. Resultados: {query.count()} registros")
            else:
                # Fallback: se não houver códigos associados, usa filtro tradicional
                query = query.filter(
                    Q(sigla_unidade__icontains=sigla) | 
                    Q(sigla__icontains=sigla) |
                    Q(denominacao_unidade__icontains=sigla)
                )
                logger.info(f"Nenhum código associado encontrado. Usando filtro tradicional: {query.count()} registros")
        
        # Aplicar os demais filtros (tipo_cargo, nivel)
        if tipo_cargo:
            query = query.filter(tipo_cargo=tipo_cargo)
            logger.info(f"Após filtro tipo_cargo={tipo_cargo}: {query.count()} registros")
            
        if nivel:
            query = query.filter(nivel=nivel)
            logger.info(f"Após filtro nivel={nivel}: {query.count()} registros")
        
        # Ordenar por sigla e nível
        query = query.order_by('sigla_unidade', '-nivel')
        
        total_registros = query.count()
        if total_registros == 0:
            logger.warning(f"Nenhum registro encontrado com os filtros: sigla={sigla}, tipo_cargo={tipo_cargo}, nivel={nivel}")
            return JsonResponse({
                'cargos': [],
                'total_itens': 0,
                'total_paginas': 1,
                'pagina_atual': pagina,
                'itens_por_pagina': tamanho
            })
        
        # Carregar os cargos do SIORG para matching
        cargos_siorg_dict = {}
        try:
            for cs in CargoSIORG.objects.all():
                key1 = f"{cs.cargo}"
                key2 = f"{cs.cargo}".replace(" ", "")
                
                import re
                match = re.match(r"(\w+)\s+(\d+)\s+(\d+)", cs.cargo)
                if match:
                    tipo, categoria, nivel_cargo = match.groups()
                    key3 = f"{tipo}{categoria}{nivel_cargo}"
                    key4 = f"{tipo}-{categoria}-{nivel_cargo}"
                    
                    cargos_siorg_dict[key1] = cs
                    cargos_siorg_dict[key2] = cs
                    cargos_siorg_dict[key3] = cs
                    cargos_siorg_dict[key4] = cs
                else:
                    cargos_siorg_dict[key1] = cs
                    cargos_siorg_dict[key2] = cs
            logger.info(f"Carregados {len(cargos_siorg_dict)} cargos SIORG para referência")
        except Exception as e:
            logger.error(f"Erro ao carregar cargos SIORG: {str(e)}")
        
        # Paginação
        paginator = Paginator(query, tamanho)
        page_obj = paginator.get_page(pagina)
        
        logger.info(f"Paginação: total_registros={total_registros}, total_paginas={paginator.num_pages}, pagina_atual={pagina}")
        
        # Converter resultados mantendo a lógica de cálculo original
        result = []
        for cargo in page_obj:
            quantidade = int(cargo.quantidade) if cargo.quantidade else 0
            categoria = int(cargo.categoria) if cargo.categoria is not None else 1
            nivel_cargo = int(cargo.nivel) if cargo.nivel is not None else 0
            
            cargo_key = f"{cargo.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{cargo.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos = 0
            valor_unitario = 0
            if cargo_siorg:
                pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
                if isinstance(cargo_siorg.valor, str):
                    try:
                        valor_str = cargo_siorg.valor.replace('R$ ', '').replace('.', '').replace(',', '.')
                        valor_unitario = float(valor_str)
                    except (ValueError, AttributeError):
                        logger.warning(f"Erro ao converter valor '{cargo_siorg.valor}' para float")
                else:
                    valor_unitario = float(cargo_siorg.valor) if cargo_siorg.valor else 0
            
            if pontos <= 0:
                pontos_padrao = {
                    18: 7.65, 17: 7.08, 16: 6.23, 15: 5.41, 14: 4.63,
                    13: 4.12, 12: 3.10, 11: 2.47, 10: 2.12, 9: 1.67,
                    8: 1.60, 7: 1.39, 6: 1.17, 5: 1.00, 4: 0.44,
                    3: 0.37, 2: 0.21, 1: 0.12,
                }
                pontos = pontos_padrao.get(nivel_cargo, 1.0)
            
            if valor_unitario <= 0:
                valor_unitario = 100.0
            
            pontos_total = pontos * quantidade
            gasto_total = pontos_total * valor_unitario
            
            result.append({
                'area': cargo.sigla_unidade or '',
                'categoria_unidade': cargo.tipo_unidade or '',
                'sigla_unidade': cargo.sigla_unidade or '',  # Campo explícito para compatibilidade
                'tipo_unidade': cargo.tipo_unidade or '',    # Campo explícito para compatibilidade
                'tipo_cargo': cargo.tipo_cargo or '',
                'denominacao': cargo.denominacao or '',
                'categoria': categoria,
                'nivel': nivel_cargo,
                'quantidade': quantidade,
                'pontos': pontos,
                'valor_unitario': valor_unitario,
                'pontos_totais': pontos_total,
                'gastos_totais': gasto_total,
                'grafo': cargo.grafo or ''  # Include grafo field for hierarchical ordering
            })
        
        logger.info(f"Dados formatados: {len(result)} registros processados")
        
        return JsonResponse({
            'cargos': result,
            'total_itens': paginator.count,
            'total_paginas': paginator.num_pages,
            'pagina_atual': pagina,
            'itens_por_pagina': tamanho
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados diretos de cargos: {str(e)}", exc_info=True)
        return JsonResponse({
            'erro': f'Ocorreu um erro ao buscar os dados: {str(e)}',
            'cargos': [],
            'total_itens': 0,
            'total_paginas': 1,
            'pagina_atual': 1,
            'itens_por_pagina': tamanho
        }, status=500)

@login_required
def comparador(request):
    """Renderiza a página do comparador de organogramas."""
    
    try:
        from .utils import estrutura_json_organograma
        from .models import UnidadeCargo, CargoSIORG
        import json
        
        # Buscar dados diretamente do banco de dados
        dados = estrutura_json_organograma()
        
        # Converter para string JSON para passar ao template
        organograma_data_json = json.dumps({
            'core_unidadecargo': dados,
            'core_cargosiorg': [
                {
                    'cargo': f"{cargo.cargo}",
                    'valor': str(cargo.valor),
                    'unitario': float(cargo.unitario)
                }
                for cargo in CargoSIORG.objects.all()
            ]
        })
        
    except Exception as e:
        # Log do erro e usar dados mínimos como fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao carregar dados do comparador: {str(e)}")
        
        organograma_data_json = json.dumps({
            "core_unidadecargo": [],
            "core_cargosiorg": []
        })
    
    return render(request, 'core/comparador.html', {
        'organograma_data': organograma_data_json
    })

@login_required(login_url="/login_direct/")
def financeira(request):
    """
    View para renderizar a página de monitoramento financeiro.
    """
    return render(request, 'core/financeira.html')

@login_required(login_url="/login_direct/")
def financeira_data_real(request):
    """
    Retorna dados financeiros REAIS do banco de dados em formato JSON.
    Utiliza os mesmos dados do organograma.
    """
    # Obtém o período da requisição
    periodo = request.GET.get('periodo', 'Mês Atual')
    
    try:
        # Importar a mesma função utilizada pelo organograma
        from .utils import estrutura_json_organograma
        import json
        from decimal import Decimal
        
        # Obter os dados do organograma, que já contém valores de gastos e pontos
        unidades_dados = estrutura_json_organograma()
        
        if not unidades_dados:
            raise Exception("Nenhuma unidade encontrada")
        
        # Agrupar dados por departamento (código_unidade) e, paralelamente,
        # acumular os totais globais (incluindo a unidade raiz 308804).

        departamentos = {}
        orcamento_total = 0.0
        executado_total = 0.0

        for linha in unidades_dados:
            cod = str(linha.get('codigo_unidade', ''))

            pontos = float(linha.get('pontos_total', 0))
            gastos = float(linha.get('gasto_total', 0))

            # Atualiza os totais globais (inclui MPO)
            orcamento_total += pontos
            executado_total += gastos

            # Para a lista de unidades queremos EXCLUIR o MPO (308804)
            if cod == '308804':
                continue

            if cod not in departamentos:
                departamentos[cod] = {
                    'codigo': cod,
                    'nome': linha.get('denominacao_unidade', 'Sem nome'),
                    'orcamento': 0.0,
                    'executado': 0.0
                }

            departamentos[cod]['orcamento'] += pontos
            departamentos[cod]['executado'] += gastos

        # Converter em lista e calcular percentuais
        unidades_financeiras = []

        for dep in departamentos.values():
            orc = dep['orcamento']
            exe = dep['executado']
            pct = (exe / orc * 100) if orc > 0 else 0

            dep['percentual'] = pct
            dep['status'] = "Crítico" if pct < 50 else ("Atenção" if pct < 80 else "Adequado")

            unidades_financeiras.append(dep)

        # Ordenar lista por Pontos (orcamento) decrescente
        unidades_financeiras.sort(key=lambda x: x['orcamento'], reverse=True)
        
        # Percentual e status gerais
        percentual = (executado_total / orcamento_total * 100) if orcamento_total > 0 else 0
        status = "Crítico" if percentual < 50 else ("Atenção" if percentual < 80 else "Adequado")
        
        # Simular dados de execução mensal (como não temos dados históricos)
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        execucao_mensal = []
        meses = []
        
        # Criar array com os últimos 6 meses
        data_atual = datetime.now()
        for i in range(5, -1, -1):
            data_mes = data_atual - relativedelta(months=i)
            meses.append(data_mes.strftime("%b/%Y"))
        
        # Calcular valor médio mensal para distribuição
        valor_medio_mensal_orcamento = orcamento_total / 6
        valor_medio_mensal_executado = executado_total / 6
        
        # Distribuir valores nos meses (de forma crescente para simular execução)
        for i, mes in enumerate(meses):
            fator = (i + 1) / 6  # Fator crescente de 1/6 até 1
            
            execucao_mensal.append({
                "mes": mes,
                "orcado": valor_medio_mensal_orcamento,
                "executado": valor_medio_mensal_executado * fator
            })
        
        # Preparação dos dados de resposta
        dados = {
            "orcamento_total": orcamento_total,
            "executado_total": executado_total,
            "percentual_execucao": percentual,
            "status": status,
            "variacao_periodo": 0.0,  # Valor real precisa ser calculado com dados históricos
            "unidades": unidades_financeiras,
            "execucao_mensal": execucao_mensal,
            "periodo": periodo
        }
        
        return JsonResponse(dados)
        
    except Exception as e:
        # Log do erro
        print(f"Erro ao processar dados financeiros reais: {str(e)}")
        
        # Em caso de erro, retornar estrutura vazia mas válida
        dados = {
            "orcamento_total": 0,
            "executado_total": 0,
            "percentual_execucao": 0,
            "status": "Não disponível",
            "variacao_periodo": 0,
            "unidades": [],
            "execucao_mensal": [],
            "periodo": periodo,
            "erro": str(e)  # Incluir mensagem de erro para depuração
        }
        
        return JsonResponse(dados)

@require_http_methods(["GET"])
def api_financeira_organograma(request):
    """API específica para a tela Financeira que devolve o mesmo JSON do organograma,
    mas em endpoint independente, evitando interferência entre páginas."""
    try:
        # Mesmo arquivo JSON utilizado pela API de organograma
        json_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'data', 'organograma.json')

        if not os.path.exists(json_path):
            return JsonResponse({
                'error': 'Arquivo organograma.json não encontrado. Execute uma atualização no Admin primeiro.'
            }, status=404)

        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        # Se dados for lista com item único, extrair
        if isinstance(dados, list) and len(dados) == 1:
            dados = dados[0]

        # Retorna dados sem modificação
        return JsonResponse(dados, safe=True)

    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Erro ao decodificar o arquivo: {str(e)}'}, status=500)
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return JsonResponse({'error': f'Erro inesperado: {str(e)}', 'stack_trace': traceback_str}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BaixarAnexoSimulacaoView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            estrutura_atual = data.get('estrutura_atual', [])
            estrutura_nova = data.get('estrutura_nova', [])

            if not isinstance(estrutura_atual, list) or not isinstance(estrutura_nova, list):
                return JsonResponse({'error': 'Invalid data format: estrutura_atual and estrutura_nova must be arrays.'}, status=400)

            # Validate data before processing
            for i, item in enumerate(estrutura_atual + estrutura_nova):
                if not isinstance(item, dict):
                    return JsonResponse({'error': f'Invalid item at position {i}: must be an object.'}, status=400)

            # Call the utility function to generate the Excel file
            excel_stream = gerar_anexo_simulacao(estrutura_atual, estrutura_nova)
            
            response = HttpResponse(
                excel_stream, 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="Anexo_Simulacao.xlsx"'
            return response

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except FileNotFoundError as e:
             return JsonResponse({'error': str(e)}, status=404) # e.g., no active template
        except ValueError as e:
            # Log the full error for debugging
            print(f"ValueError in BaixarAnexoSimulacaoView: {str(e)}")
            if "invalid literal for int()" in str(e):
                return JsonResponse({'error': 'Erro de conversão de dados. Verifique se todos os campos numéricos estão preenchidos corretamente.'}, status=400)
            return JsonResponse({'error': str(e)}, status=400) # e.g., template sheet missing or multiple active
        except Exception as e:
            # Log the exception e for debugging
            print(f"Error in BaixarAnexoSimulacaoView: {str(e)}") # Basic logging
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET"])
def listar_simulacoes(request):
    """Lista todas as simulações salvas do usuário atual"""
    simulacoes = SimulacaoSalva.objects.filter(usuario=request.user)
    
    data = []
    for sim in simulacoes:
        data.append({
            'id': sim.id,
            'nome': sim.nome,
            'descricao': sim.descricao or '',
            'unidade_base': sim.unidade_base or '',
            'criado_em': sim.criado_em.strftime('%d/%m/%Y %H:%M'),
            'atualizado_em': sim.atualizado_em.strftime('%d/%m/%Y %H:%M')
        })
    
    return JsonResponse({
        'simulacoes': data,
        'total': len(data),
        'limite': 5
    })

@login_required
@require_http_methods(["POST"])
def salvar_simulacao(request):
    """Salva uma nova simulação ou atualiza uma existente"""
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        dados_estrutura = data.get('dados_estrutura', [])
        unidade_base = data.get('unidade_base', '').strip()
        simulacao_id = data.get('id')  # Para atualização
        
        # Validações
        if not nome:
            return JsonResponse({'erro': 'Nome da simulação é obrigatório'}, status=400)
        
        if not dados_estrutura:
            return JsonResponse({'erro': 'Dados da estrutura são obrigatórios'}, status=400)
        
        # Verificar se é atualização ou criação
        if simulacao_id:
            # Atualização
            try:
                simulacao = SimulacaoSalva.objects.get(id=simulacao_id, usuario=request.user)
                simulacao.nome = nome
                simulacao.descricao = descricao
                simulacao.dados_estrutura = dados_estrutura
                simulacao.unidade_base = unidade_base
                simulacao.save()
                
                return JsonResponse({
                    'mensagem': 'Simulação atualizada com sucesso',
                    'id': simulacao.id
                })
            except SimulacaoSalva.DoesNotExist:
                return JsonResponse({'erro': 'Simulação não encontrada'}, status=404)
        else:
            # Criação
            # Verificar limite de 5 simulações
            total_simulacoes = SimulacaoSalva.objects.filter(usuario=request.user).count()
            if total_simulacoes >= 5:
                return JsonResponse({
                    'erro': 'Limite de 5 simulações atingido. Delete uma simulação existente antes de criar uma nova.'
                }, status=400)
            
            # Verificar se já existe simulação com mesmo nome
            if SimulacaoSalva.objects.filter(usuario=request.user, nome=nome).exists():
                return JsonResponse({
                    'erro': f'Já existe uma simulação com o nome "{nome}"'
                }, status=400)
            
            simulacao = SimulacaoSalva.objects.create(
                usuario=request.user,
                nome=nome,
                descricao=descricao,
                dados_estrutura=dados_estrutura,
                unidade_base=unidade_base
            )
            
            return JsonResponse({
                'mensagem': 'Simulação salva com sucesso',
                'id': simulacao.id
            }, status=201)
            
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def carregar_simulacao(request, simulacao_id):
    """Carrega os dados de uma simulação específica"""
    try:
        simulacao = SimulacaoSalva.objects.get(id=simulacao_id, usuario=request.user)
        
        return JsonResponse({
            'id': simulacao.id,
            'nome': simulacao.nome,
            'descricao': simulacao.descricao or '',
            'dados_estrutura': simulacao.dados_estrutura,
            'unidade_base': simulacao.unidade_base or '',
            'criado_em': simulacao.criado_em.strftime('%d/%m/%Y %H:%M'),
            'atualizado_em': simulacao.atualizado_em.strftime('%d/%m/%Y %H:%M')
        })
    except SimulacaoSalva.DoesNotExist:
        return JsonResponse({'erro': 'Simulação não encontrada'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def deletar_simulacao(request, simulacao_id):
    """Deleta uma simulação do usuário"""
    try:
        simulacao = SimulacaoSalva.objects.get(id=simulacao_id, usuario=request.user)
        nome = simulacao.nome
        simulacao.delete()
        
        return JsonResponse({
            'mensagem': f'Simulação "{nome}" deletada com sucesso'
        })
    except SimulacaoSalva.DoesNotExist:
        return JsonResponse({'erro': 'Simulação não encontrada'}, status=404)
