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
from .models import (
    UnidadeCargo, 
    CargoSIORG, 
    SimulacaoSalva, 
    TipoUsuario, 
    SolicitacaoSimulacao, 
    NotificacaoSimulacao
)
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
from django.contrib.auth.models import User, Group


# Funções auxiliares para lógica hierárquica de contagem de funcionários
def identificar_tipo_no(sigla_unidade):
    """
    Identifica se um nó é pai (secretaria) ou agregador (superior).
    """
    # Buscar o nó na tabela UnidadeCargo
    no = UnidadeCargo.objects.filter(sigla_unidade=sigla_unidade).first()
    
    if not no:
        return None, None
    
    # Verificar se é um nó agregador (tem múltiplos filhos diretos)
    # Filhos diretos são nós que contêm o código do nó pai no grafo
    filhos_diretos = UnidadeCargo.objects.filter(
        grafo__contains=f"-{no.codigo_unidade}-"
    ).exclude(codigo_unidade=no.codigo_unidade)
    
    # Filtrar apenas os filhos diretos únicos (não netos e sem duplicatas)
    filhos_reais = {}
    for filho in filhos_diretos:
        # Verificar se é filho direto (não tem outros códigos entre o pai e o filho)
        grafo_filho = filho.grafo
        codigos_grafo = grafo_filho.split('-')
        
        # Encontrar a posição do código do pai no grafo
        try:
            pos_pai = codigos_grafo.index(str(no.codigo_unidade))
            # Se o código do filho está logo após o código do pai, é filho direto
            if pos_pai + 1 < len(codigos_grafo) and codigos_grafo[pos_pai + 1] == str(filho.codigo_unidade):
                # Usar sigla_unidade como chave para evitar duplicatas
                filhos_reais[filho.sigla_unidade] = filho
        except ValueError:
            continue
    
    # Converter para lista
    filhos_reais_lista = list(filhos_reais.values())
    
    # Verificar se é um nó agregador (tem múltiplos filhos diretos)
    if len(filhos_reais_lista) > 1:
        return "AGREGADOR", no
    elif len(filhos_reais_lista) == 1:
        # Se tem apenas 1 filho, verificar se esse filho tem filhos
        filho = filhos_reais_lista[0]
        netos = UnidadeCargo.objects.filter(
            grafo__contains=f"-{filho.codigo_unidade}-"
        ).exclude(codigo_unidade=filho.codigo_unidade)
        
        if netos.count() > 0:
            return "AGREGADOR", no
        else:
            return "PAI", no
    else:
        # Se não tem filhos diretos, é um nó pai
        return "PAI", no

def contar_funcionarios_no_pai(sigla_unidade):
    """
    Conta funcionários de um nó pai usando a coluna 'diretoria' ou 'coordenacao'.
    Tenta primeiro 'diretoria', depois 'coordenacao'.
    Inclui tratamento especial para casos onde a secretaria contém MPO/SIGLA.
    """
    from .models import RelatorioGratificacoes
    from django.db.models import Q
    
    # Construir filtros robustos que incluem variações MPO/SIGLA
    diretoria_filter = Q(diretoria=sigla_unidade)
    coordenacao_filter = Q(coordenacao=sigla_unidade)
    
    # Tratamento especial para casos MPO/SIGLA (adiciona busca por secretaria também)
    if sigla_unidade:
        # Buscar por variações MPO/SIGLA em qualquer campo relevante
        mpo_pattern = f"MPO/{sigla_unidade}"
        diretoria_filter |= Q(diretoria=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(coordenacao=mpo_pattern)
        coordenacao_filter |= Q(coordenacao=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(diretoria=mpo_pattern)
    
    # Contar por diretoria (incluindo todas as variações)
    count_diretoria = RelatorioGratificacoes.objects.filter(diretoria_filter).count()
    
    # Contar por coordenacao (incluindo todas as variações)
    count_coordenacao = RelatorioGratificacoes.objects.filter(coordenacao_filter).count()
    
    # Retornar o maior valor (priorizar diretoria se igual)
    return max(count_diretoria, count_coordenacao)

def contar_funcionarios_no_agregador(sigla_unidade, no_agregador):
    """
    Conta funcionários de um nó agregador somando:
    1. Funcionários próprios (coordenacao/diretoria)
    2. Funcionários de TODOS os descendentes na árvore hierárquica
    """
    # 1. Contar funcionários próprios do nó agregador
    funcionarios_proprios = contar_funcionarios_no_pai(sigla_unidade)
    
    # 2. Encontrar TODOS os descendentes (não apenas filhos diretos)
    # Buscar todos os nós que têm o código do agregador no seu grafo
    todos_descendentes = UnidadeCargo.objects.filter(
        grafo__contains=f"-{no_agregador.codigo_unidade}-"
    ).exclude(codigo_unidade=no_agregador.codigo_unidade)
    
    # 3. Contar funcionários de todos os descendentes (sem duplicatas por sigla)
    descendentes_unicos = {}
    for descendente in todos_descendentes:
        sigla_desc = descendente.sigla_unidade
        if sigla_desc not in descendentes_unicos:
            descendentes_unicos[sigla_desc] = descendente
    
    # 4. Somar funcionários de todos os descendentes
    total_descendentes = 0
    for sigla_desc, descendente in descendentes_unicos.items():
        # Contar funcionários diretos do descendente (sem recursão para evitar loop)
        funcionarios_desc = contar_funcionarios_no_pai(sigla_desc)
        total_descendentes += funcionarios_desc
    
    # 5. Somar funcionários próprios + todos os descendentes
    return funcionarios_proprios + total_descendentes

def contar_funcionarios_unidade(sigla_unidade):
    """
    Conta funcionários de uma unidade usando a lógica hierárquica.
    """
    tipo_no, no = identificar_tipo_no(sigla_unidade)
    
    if tipo_no == "PAI":
        return contar_funcionarios_no_pai(sigla_unidade)
    elif tipo_no == "AGREGADOR":
        return contar_funcionarios_no_pai(sigla_unidade)  # Usar apenas funcionários próprios, não somar descendentes
    else:
        return 0


def contar_gsiste_no_pai(sigla_unidade):
    """
    Conta funcionários com GSISTE (qualquer valor exceto GSISP) de um nó pai.
    GSISTE inclui: G.SPO, GSISTE.CF, G.SISG, G.SIPEC
    """
    from .models import RelatorioGratificacoes
    from django.db.models import Q
    
    # Construir filtros robustos que incluem variações MPO/SIGLA
    # GSISTE = qualquer valor exceto 'GSISP'
    diretoria_filter = Q(diretoria=sigla_unidade) & ~Q(gsiste='GSISP') & ~Q(gsiste='')
    coordenacao_filter = Q(coordenacao=sigla_unidade) & ~Q(gsiste='GSISP') & ~Q(gsiste='')
    
    # Tratamento especial para casos MPO/SIGLA (adiciona busca por secretaria também)
    if sigla_unidade:
        # Buscar por variações MPO/SIGLA em qualquer campo relevante
        mpo_pattern = f"MPO/{sigla_unidade}"
        diretoria_filter |= (Q(diretoria=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(coordenacao=mpo_pattern)) & ~Q(gsiste='GSISP') & ~Q(gsiste='')
        coordenacao_filter |= (Q(coordenacao=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(diretoria=mpo_pattern)) & ~Q(gsiste='GSISP') & ~Q(gsiste='')
    
    # Contar por diretoria (incluindo todas as variações)
    count_diretoria = RelatorioGratificacoes.objects.filter(diretoria_filter).count()
    
    # Contar por coordenacao (incluindo todas as variações)
    count_coordenacao = RelatorioGratificacoes.objects.filter(coordenacao_filter).count()
    
    # Retornar o maior valor (priorizar diretoria se igual)
    return max(count_diretoria, count_coordenacao)


def contar_gsisp_no_pai(sigla_unidade):
    """
    Conta funcionários com GSISTE = 'GSISP' de um nó pai usando a mesma lógica de contagem.
    """
    from .models import RelatorioGratificacoes
    from django.db.models import Q
    
    # Construir filtros robustos que incluem variações MPO/SIGLA
    diretoria_filter = Q(diretoria=sigla_unidade) & Q(gsiste='GSISP')
    coordenacao_filter = Q(coordenacao=sigla_unidade) & Q(gsiste='GSISP')
    
    # Tratamento especial para casos MPO/SIGLA (adiciona busca por secretaria também)
    if sigla_unidade:
        # Buscar por variações MPO/SIGLA em qualquer campo relevante
        mpo_pattern = f"MPO/{sigla_unidade}"
        diretoria_filter |= (Q(diretoria=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(coordenacao=mpo_pattern)) & Q(gsiste='GSISP')
        coordenacao_filter |= (Q(coordenacao=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(diretoria=mpo_pattern)) & Q(gsiste='GSISP')
    
    # Contar por diretoria (incluindo todas as variações)
    count_diretoria = RelatorioGratificacoes.objects.filter(diretoria_filter).count()
    
    # Contar por coordenacao (incluindo todas as variações)
    count_coordenacao = RelatorioGratificacoes.objects.filter(coordenacao_filter).count()
    
    # Retornar o maior valor (priorizar diretoria se igual)
    return max(count_diretoria, count_coordenacao)


def contar_gsiste_nivel_no_pai(sigla_unidade, nivel_tipo):
    """
    Conta funcionários com GSISTE_NIVEL específico (NI ou NS) de um nó pai.
    nivel_tipo pode ser 'NI' ou 'NS'.
    """
    from .models import RelatorioGratificacoes
    from django.db.models import Q
    
    # Construir filtros robustos que incluem variações MPO/SIGLA
    diretoria_filter = Q(diretoria=sigla_unidade) & Q(gsiste_nivel=nivel_tipo)
    coordenacao_filter = Q(coordenacao=sigla_unidade) & Q(gsiste_nivel=nivel_tipo)
    
    # Tratamento especial para casos MPO/SIGLA (adiciona busca por secretaria também)
    if sigla_unidade:
        # Buscar por variações MPO/SIGLA em qualquer campo relevante
        mpo_pattern = f"MPO/{sigla_unidade}"
        diretoria_filter |= (Q(diretoria=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(coordenacao=mpo_pattern)) & Q(gsiste_nivel=nivel_tipo)
        coordenacao_filter |= (Q(coordenacao=mpo_pattern) | Q(secretaria=mpo_pattern) | Q(diretoria=mpo_pattern)) & Q(gsiste_nivel=nivel_tipo)
    
    # Contar por diretoria (incluindo todas as variações)
    count_diretoria = RelatorioGratificacoes.objects.filter(diretoria_filter).count()
    
    # Contar por coordenacao (incluindo todas as variações)
    count_coordenacao = RelatorioGratificacoes.objects.filter(coordenacao_filter).count()
    
    # Retornar o maior valor (priorizar diretoria se igual)
    return max(count_diretoria, count_coordenacao)


def contar_gsiste_unidade(sigla_unidade):
    """
    Conta funcionários com GSISTE (qualquer valor exceto GSISP) de uma unidade usando a lógica hierárquica.
    """
    tipo_no, no = identificar_tipo_no(sigla_unidade)
    
    if tipo_no == "PAI":
        return contar_gsiste_no_pai(sigla_unidade)
    elif tipo_no == "AGREGADOR":
        return contar_gsiste_no_pai(sigla_unidade)  # Usar apenas funcionários próprios, não somar descendentes
    else:
        return 0


def contar_gsisp_unidade(sigla_unidade):
    """
    Conta funcionários com GSISTE = 'GSISP' de uma unidade usando a lógica hierárquica.
    """
    tipo_no, no = identificar_tipo_no(sigla_unidade)
    
    if tipo_no == "PAI":
        return contar_gsisp_no_pai(sigla_unidade)
    elif tipo_no == "AGREGADOR":
        return contar_gsisp_no_pai(sigla_unidade)  # Usar apenas funcionários próprios, não somar descendentes
    else:
        return 0


def contar_gsiste_nivel_unidade(sigla_unidade, nivel_tipo):
    """
    Conta funcionários com GSISTE_NIVEL específico de uma unidade usando a lógica hierárquica.
    nivel_tipo pode ser 'NI' ou 'NS'.
    """
    tipo_no, no = identificar_tipo_no(sigla_unidade)
    
    if tipo_no == "PAI":
        return contar_gsiste_nivel_no_pai(sigla_unidade, nivel_tipo)
    elif tipo_no == "AGREGADOR":
        return contar_gsiste_nivel_no_pai(sigla_unidade, nivel_tipo)  # Usar apenas funcionários próprios, não somar descendentes
    else:
        return 0


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
        
        json_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'organograma.json')
        
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
        json_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'organograma.json')
        
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
    json_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'organograma.json')
    
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
        # Consulta base - TODOS os cargos (removendo filtro por usuário para mostrar estado completo)
        from django.db.models import Q
        query = UnidadeCargo.objects.all()
        logger.info(f"Total de registros disponíveis: {query.count()}")
        
        # Se houver sigla, aplicar filtro especial
        if sigla:
            logger.info(f"Iniciando processamento de filtro por sigla: {sigla}")
            
            # Buscamos registros onde a sigla aparece EXATAMENTE (não parcialmente)
            codigos_associados = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla) | 
                Q(sigla__iexact=sigla)
            ).values_list('codigo_unidade', flat=True).distinct()
            
            codigos_lista = list(codigos_associados)
            logger.info(f"Códigos de unidade associados à sigla '{sigla}': {codigos_lista[:10]} (total: {len(codigos_lista)})")
            
            if codigos_lista:
                # Filtro correto: incluir a própria unidade E TODA a árvore subordinada
                filtros_hierarquicos = []
                for code in codigos_lista:
                    # Incluir a própria unidade
                    filtros_hierarquicos.append(Q(codigo_unidade=code))
                    # Incluir TODA a árvore subordinada (qualquer grafo que contenha este código seguido de hífen)
                    filtros_hierarquicos.append(Q(grafo__contains=f"-{code}-"))
                    # Incluir subordinadas diretas (grafo começa com o código seguido de hífen)
                    filtros_hierarquicos.append(Q(grafo__startswith=f"{code}-"))
                
                query = query.filter(reduce(operator.or_, filtros_hierarquicos))
                logger.info(f"Filtrando registros hierárquicos completos para códigos {codigos_lista}. Resultados: {query.count()} registros")
            else:
                # Fallback: se não houver códigos associados, usa filtro tradicional EXATO
                query = query.filter(
                    Q(sigla_unidade__iexact=sigla) | 
                    Q(sigla__iexact=sigla)
                )
                logger.info(f"Nenhum código associado encontrado. Usando filtro tradicional EXATO: {query.count()} registros")
        
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
            
            if valor_unitario <= 0:
                valor_unitario = 100.0
            
            pontos_total = pontos * quantidade
            gasto_total = pontos_total * valor_unitario
            
            result.append({
                'id': cargo.id,  # ID do cargo
                'area': cargo.sigla_unidade or '',
                'categoria_unidade': cargo.tipo_unidade or '',
                'sigla_unidade': cargo.sigla_unidade or '',  # Campo explícito para compatibilidade
                'tipo_unidade': cargo.tipo_unidade or '',    # Campo explícito para compatibilidade
                'denominacao_unidade': cargo.denominacao_unidade or '',  # Campo para hierarquia
                'nivel_hierarquico': cargo.nivel_hierarquico or 0,  # Campo para hierarquia
                'tipo_cargo': cargo.tipo_cargo or '',
                'denominacao': cargo.denominacao or '',
                'categoria': categoria,
                'nivel': nivel_cargo,
                'quantidade': quantidade,
                'pontos': pontos,
                'valor_unitario': valor_unitario,
                'pontos_total': pontos_total,
                'gastos_totais': gasto_total,
                'grafo': cargo.grafo or '',  # Include grafo field for hierarchical ordering
                'is_manual': cargo.usuario is not None,  # ✅ MARCAR SE É CARGO MANUAL
                'manual_id': cargo.id if cargo.usuario is not None else None  # ✅ ID PARA REMOÇÃO
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
        json_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'organograma.json')

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

            # Debug: log data before processing
            print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_atual length: {len(estrutura_atual)}")
            print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_nova length: {len(estrutura_nova)}")
            if estrutura_atual:
                print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_atual[0] keys: {list(estrutura_atual[0].keys())}")
            if estrutura_nova:
                print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_nova[0] keys: {list(estrutura_nova[0].keys())}")
            
            # Debug: log data before processing
            print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_atual length: {len(estrutura_atual)}")
            print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_nova length: {len(estrutura_nova)}")
            if estrutura_atual:
                print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_atual[0] keys: {list(estrutura_atual[0].keys())}")
            if estrutura_nova:
                print(f"DEBUG: BaixarAnexoSimulacaoView - estrutura_nova[0] keys: {list(estrutura_nova[0].keys())}")
            
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
    """Lista simulações baseado no tipo de usuário"""
    from .models import obter_tipo_usuario
    
    user = request.user
    tipo_usuario = obter_tipo_usuario(user)
    
    # LOG DE DEBUG PARA VERIFICAR DETECÇÃO DE GERENTE
    print(f"🐛 DEBUG: Usuário: {user.username} ({user.email})")
    print(f"🐛 DEBUG: Tipo detectado: {tipo_usuario}")
    print(f"🐛 DEBUG: É superuser: {user.is_superuser}")
    print(f"🐛 DEBUG: Grupos do usuário: {[g.name for g in user.groups.all()]}")
    
    # Se for gerente, pode ver TODAS as simulações do sistema
    if tipo_usuario == 'gerente':
        print(f"🐛 DEBUG: GERENTE DETECTADO! Carregando TODAS as simulações")
        simulacoes = SimulacaoSalva.objects.all().order_by('-atualizado_em')
    else:
        print(f"🐛 DEBUG: Usuário normal. Carregando apenas simulações próprias")
        # Usuários normais veem apenas suas próprias simulações
        simulacoes = SimulacaoSalva.objects.filter(usuario=user)
    
    data = []
    for sim in simulacoes:
        is_owner = sim.usuario == user
        
        # Para simulações de análise, verificar se o usuário criador é realmente interno
        if not is_owner and sim.status == 'enviada_analise':
            if sim.tipo_usuario_atual != 'interno':
                continue  # Pular simulações de usuários que não são internos
        
        data.append({
            'id': sim.id,
            'nome': sim.nome,
            'descricao': sim.descricao or '',
            'unidade_base': sim.unidade_base or '',
            'status': sim.get_status_display(),
            'status_code': sim.status,
            'tipo_usuario': sim.get_tipo_usuario_display_atual(),  # Usar o método dinâmico
            'usuario': sim.usuario.get_full_name() or sim.usuario.username if not is_owner else 'Você',
            'usuario_email': sim.usuario.email if not is_owner else '',
            'is_owner': is_owner,
            'pode_enviar_analise': is_owner and sim.status in ['rascunho', 'rejeitada', 'rejeitada_editada'] and sim.tipo_usuario_atual == 'interno',  # Usar propriedade dinâmica
            'pode_avaliar': not is_owner and tipo_usuario == 'gerente' and sim.status in ['enviada_analise', 'rejeitada', 'rejeitada_editada'],
            'criado_em': sim.criado_em.strftime('%d/%m/%Y %H:%M'),
            'atualizado_em': sim.atualizado_em.strftime('%d/%m/%Y %H:%M')
        })
    
    return JsonResponse({
        'simulacoes': data,
        'total': len(data),
        'limite': None if tipo_usuario == 'gerente' else 5,
        'user_type': tipo_usuario,
        'is_gerente': tipo_usuario == 'gerente'
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
            # Verificar limite de 5 simulações (não se aplica a gerentes)
            from .models import obter_tipo_usuario
            if obter_tipo_usuario(request.user) != 'gerente':
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
        from .models import obter_tipo_usuario
        
        user = request.user
        tipo_usuario = obter_tipo_usuario(user)
        
        # Lógica de permissões baseada no tipo de usuário
        if tipo_usuario == 'gerente':
            # Gerentes podem carregar QUALQUER simulação
            simulacao = SimulacaoSalva.objects.get(id=simulacao_id)
        else:
            # Usuários normais só podem carregar simulações próprias
            simulacao = SimulacaoSalva.objects.get(id=simulacao_id, usuario=user)
        
        return JsonResponse({
            'id': simulacao.id,
            'nome': simulacao.nome,
            'descricao': simulacao.descricao or '',
            'dados_estrutura': simulacao.dados_estrutura,
            'unidade_base': simulacao.unidade_base or '',
            'criado_em': simulacao.criado_em.strftime('%d/%m/%Y %H:%M'),
            'atualizado_em': simulacao.atualizado_em.strftime('%d/%m/%Y %H:%M'),
            'usuario': simulacao.usuario.get_full_name() or simulacao.usuario.username,
            'status': simulacao.get_status_display(),
            'tipo_usuario_autor': simulacao.tipo_usuario_atual
        })
    except SimulacaoSalva.DoesNotExist:
        return JsonResponse({'erro': 'Simulação não encontrada ou sem permissão de acesso'}, status=404)

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


@login_required
@require_http_methods(["PUT", "PATCH"])
def atualizar_simulacao(request, simulacao_id):
    """View para atualizar uma simulação existente (auto-save)"""
    import json
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from .models import SimulacaoSalva, obter_tipo_usuario
    
    try:
        # Verificar se usuário tem permissão para editar
        simulacao = get_object_or_404(SimulacaoSalva, id=simulacao_id)
        
        # Verificar permissões
        if simulacao.usuario != request.user:
            # Verificar se é gerente e pode editar simulações enviadas para análise
            user_tipo = obter_tipo_usuario(request.user)
            if user_tipo != 'gerente' or simulacao.status not in ['enviada_analise', 'rejeitada', 'rejeitada_editada']:
                return JsonResponse({'success': False, 'message': 'Você não tem permissão para editar esta simulação'}, status=403)
        
        # Parse dos dados JSON
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        if 'dados_estrutura' not in data:
            return JsonResponse({'success': False, 'message': 'Dados da estrutura são obrigatórios'}, status=400)
        
        # Atualizar campos opcionais se fornecidos
        if 'nome' in data:
            simulacao.nome = data['nome']
        if 'descricao' in data:
            simulacao.descricao = data['descricao']
        if 'unidade_base' in data:
            simulacao.unidade_base = data['unidade_base']
        
        # Atualizar dados da estrutura
        simulacao.dados_estrutura = data['dados_estrutura']
        
        # Se simulação foi rejeitada e está sendo editada, marcar como rejeitada_editada
        if simulacao.status == 'rejeitada':
            simulacao.status = 'rejeitada_editada'
        
        simulacao.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Simulação atualizada com sucesso',
            'simulacao': {
                'id': simulacao.id,
                'nome': simulacao.nome,
                'descricao': simulacao.descricao,
                'status': simulacao.get_status_display(),
                'status_code': simulacao.status,
                'atualizado_em': simulacao.atualizado_em.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao atualizar simulação {simulacao_id}: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'}, status=500)


# === VIEWS PARA SISTEMA DE RELATÓRIOS ===

@login_required
def relatorios(request):
    """
    Página principal do sistema de relatórios.
    Inclui todas as funcionalidades solicitadas.
    """
    from .models import RelatorioGratificacoes, RelatorioOrgaosCentrais, RelatorioEfetivo, UnidadeCargo
    from django.db.models import Count, Sum, Avg
    
    context = {}
    
    # Dados para o relatório de pontos e gratificações
    try:
        # Estatísticas básicas
        total_servidores = RelatorioGratificacoes.objects.count()
        total_unidades = RelatorioGratificacoes.objects.values('unidade_lotacao').distinct().count()
        total_cargos = RelatorioGratificacoes.objects.values('cargo').distinct().count()
        
        # Dados por unidade para cálculo dos índices
        unidades_data = RelatorioGratificacoes.objects.values(
            'unidade_lotacao', 'sigla_unidade'
        ).annotate(
            total_servidores=Count('id'),
            cargos_unicos=Count('cargo', distinct=True)
        ).order_by('-total_servidores')
        
        # Dados do organograma para cálculo de pontos
        pontos_data = UnidadeCargo.objects.values(
            'denominacao_unidade', 'sigla_unidade'
        ).annotate(
            total_pontos=Sum('pontos_total'),
            total_quantidade=Sum('quantidade')
        ).filter(total_pontos__gt=0)
        
        context.update({
            'total_servidores': total_servidores,
            'total_unidades': total_unidades,
            'total_cargos': total_cargos,
            'unidades_data': list(unidades_data),
            'pontos_data': list(pontos_data),
        })
        
    except Exception as e:
        context['erro_dados'] = f"Erro ao carregar dados: {str(e)}"
    
    return render(request, 'core/relatorios.html', context)


@login_required
@require_http_methods(["GET"])
def api_relatorio_pontos_gratificacoes(request):
    """
    API para dados do relatório de pontos e gratificações.
    Primeira tabela: Unidade, Pontos totais (sem GSISTE/GSISP por enquanto)
    """
    try:
        # Parâmetros de filtro e paginação
        filtro_unidade = request.GET.get('unidade', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 11))
        
        # Criar chave de cache única baseada nos filtros
        cache_key = f"gratificacoes_data_{filtro_unidade}_{hash(filtro_unidade)}"
        
        # Tentar buscar dados do cache primeiro
        dados_cache = cache.get(cache_key)
        if dados_cache is not None:
            # Dados em cache encontrados - aplicar apenas paginação
            tabela_final = dados_cache
            total_registros = len(tabela_final)
            total_pages = (total_registros + per_page - 1) // per_page
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            dados_paginados = tabela_final[start_index:end_index]
            
            return JsonResponse({
                'status': 'success',
                'data': dados_paginados,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_registros': total_registros,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                },
                'filtros': {
                    'unidade': filtro_unidade,
                    'total_registros': total_registros
                }
            })
        
        # Se não há cache, processar dados completos
        from django.db.models import Q
        from functools import reduce
        import operator
        
        # Consulta base
        query = UnidadeCargo.objects.all()
        
        # Aplicar filtro de unidade com busca hierárquica se fornecido
        if filtro_unidade:
            # Busca hierárquica: encontrar códigos associados à sigla/unidade
            sigla_upper = filtro_unidade.upper()
            codigos_associados = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla_upper) | 
                Q(sigla__iexact=sigla_upper) |
                Q(denominacao_unidade__icontains=filtro_unidade)
            ).values_list('codigo_unidade', flat=True).distinct()
            
            codigos_lista = list(codigos_associados)
            
            if codigos_lista:
                # Filtro hierárquico: incluir unidade E toda árvore subordinada
                filtros_hierarquicos = []
                for code in codigos_lista:
                    # Incluir a própria unidade
                    filtros_hierarquicos.append(Q(codigo_unidade=code))
                    # Incluir TODA a árvore subordinada
                    filtros_hierarquicos.append(Q(grafo__contains=f"-{code}-"))
                    # Incluir subordinadas diretas
                    filtros_hierarquicos.append(Q(grafo__startswith=f"{code}-"))
                
                query = query.filter(reduce(operator.or_, filtros_hierarquicos))
            else:
                # Fallback para busca por nome
                query = query.filter(
                    Q(denominacao_unidade__icontains=filtro_unidade) |
                    Q(sigla_unidade__icontains=filtro_unidade)
                )
        
        # Carregar os cargos do SIORG para matching (mesma lógica do Comparador)
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
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao carregar cargos SIORG: {str(e)}")
        
        # Agrupar dados por unidade
        unidades_dados = {}
        for registro in query:
            unidade = registro.denominacao_unidade or registro.sigla_unidade or 'Unidade não identificada'
            quantidade = int(registro.quantidade or 0)
            
            # Calcular pontos usando a mesma lógica do Comparador
            categoria = int(registro.categoria) if registro.categoria is not None else 1
            nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
            
            cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos = 0
            if cargo_siorg:
                pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
            
            pontos_total = pontos * quantidade
            
            if unidade in unidades_dados:
                unidades_dados[unidade]['pontos'] += pontos_total
            else:
                # Extrair sigla da unidade para usar nas contagens
                sigla_unidade = extrair_sigla_unidade(unidade)
                
                # Contar GSISTE (qualquer valor exceto GSISP: G.SPO, GSISTE.CF, G.SISG, G.SIPEC)
                gsiste_count = contar_gsiste_unidade(sigla_unidade)
                
                # Contar GSISP (apenas GSISTE = 'GSISP')
                gsisp_count = contar_gsisp_unidade(sigla_unidade)
                
                # Contar GSISTE_NIVEL (NI e NS)
                ni_count = contar_gsiste_nivel_unidade(sigla_unidade, 'NI')
                ns_count = contar_gsiste_nivel_unidade(sigla_unidade, 'NS')
                
                unidades_dados[unidade] = {
                    'unidade': unidade,
                    'pontos': pontos_total,
                    'gsist': gsiste_count,  # Contagem real de GSISTE (G.SPO, GSISTE.CF, G.SISG, G.SIPEC)
                    'gsisp': gsisp_count,   # Contagem real de GSISP
                    'ns': ns_count,         # Contagem real de GSISTE_NIVEL = 'NS'
                    'ni': ni_count          # Contagem real de GSISTE_NIVEL = 'NI'
                }
        
        # Converter para lista e ordenar
        tabela_final = list(unidades_dados.values())
        tabela_final.sort(key=lambda x: x['unidade'])
        
        # Arredondar pontos
        for item in tabela_final:
            item['pontos'] = round(item['pontos'], 2)
        
        # Salvar dados no cache por 30 minutos (1800 segundos)
        cache.set(cache_key, tabela_final, 1800)
        
        # Implementar paginação
        total_registros = len(tabela_final)
        total_pages = (total_registros + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        dados_paginados = tabela_final[start_index:end_index]
        
        return JsonResponse({
            'status': 'success',
            'data': dados_paginados,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_registros': total_registros,
                'has_next': page < total_pages,
                'has_previous': page > 1
            },
            'filtros': {
                'unidade': filtro_unidade,
                'total_registros': total_registros
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar dados de gratificações: {str(e)}'
        }, status=500)



@login_required
@require_http_methods(["GET"])
def api_relatorio_idp(request):
    """
    API específica para relatório IDP.
    PADRONIZADA COM IEE - usa exatamente a mesma lógica de pontos e colaboradores.
    """
    try:
        # Parâmetros de filtro e paginação  
        filtro_unidade = request.GET.get('unidade', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 11))
        
        # Criar chave de cache única baseada nos filtros
        cache_key = f"idp_data_{filtro_unidade}_{hash(filtro_unidade)}"
        
        # Tentar buscar dados do cache primeiro
        dados_cache = cache.get(cache_key)
        if dados_cache is not None:
            # Dados em cache encontrados - aplicar apenas paginação
            tabela_final = dados_cache
            total_registros = len(tabela_final)
            total_pages = (total_registros + per_page - 1) // per_page
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            dados_paginados = tabela_final[start_index:end_index]
            
            return JsonResponse({
                'status': 'success',
                'data': dados_paginados,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_registros': total_registros,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                },
                'filtros': {
                    'unidade': filtro_unidade,
                    'total_registros': total_registros
                }
            })
        
        # Se não há cache, processar dados completos
        from django.db.models import Q
        from functools import reduce
        import operator
        
        # Consulta base
        query = UnidadeCargo.objects.all()
        
        # Aplicar filtro de unidade com busca hierárquica se fornecido (IGUAL AO IEE)
        if filtro_unidade:
            # Busca hierárquica: encontrar códigos associados à sigla/unidade
            sigla_upper = filtro_unidade.upper()
            codigos_associados = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla_upper) | 
                Q(sigla__iexact=sigla_upper)
            ).values_list('codigo_unidade', flat=True).distinct()
            
            codigos_lista = list(codigos_associados)
            
            if codigos_lista:
                # Filtro hierárquico: incluir unidade E toda árvore subordinada
                filtros_hierarquicos = []
                for code in codigos_lista:
                    # Incluir a própria unidade
                    filtros_hierarquicos.append(Q(codigo_unidade=code))
                    # Incluir TODA a árvore subordinada
                    filtros_hierarquicos.append(Q(grafo__contains=f"-{code}-"))
                    # Incluir subordinadas diretas
                    filtros_hierarquicos.append(Q(grafo__startswith=f"{code}-"))
                
                query = query.filter(reduce(operator.or_, filtros_hierarquicos))
            else:
                # Fallback para busca por nome
                query = query.filter(
                    Q(denominacao_unidade__icontains=filtro_unidade) |
                    Q(sigla_unidade__icontains=filtro_unidade)
                )
        
        # Carregar os cargos do SIORG para matching (IGUAL AO IEE)
        cargos_siorg_dict = {}
        try:
            for cs in CargoSIORG.objects.all():
                key1 = f"{cs.cargo}"
                key2 = f"{cs.cargo}".replace(" ", "")
                
                import re
                parts = re.split(r'\s+', cs.cargo)
                if len(parts) >= 3:
                    tipo_cargo = ' '.join(parts[:-2])
                    categoria = parts[-2]
                    nivel = parts[-1]
                    
                    key3 = f"{tipo_cargo} {categoria} {nivel}"
                    key4 = f"{tipo_cargo}{categoria}{nivel}"
                    key5 = f"{tipo_cargo}{categoria}{nivel:0>2}"
                    
                    for key in [key1, key2, key3, key4, key5]:
                        cargos_siorg_dict[key] = cs
        except Exception as e:
            pass
        
        # Primeiro, calcular pontos por unidade
        unidades_pontos = {}
        for registro in query:
            unidade = registro.denominacao_unidade or registro.sigla_unidade or 'Unidade não identificada'
            quantidade = int(registro.quantidade or 0)
            
            # Calcular pontos usando a mesma lógica do Comparador
            categoria = int(registro.categoria) if registro.categoria is not None else 1
            nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
            
            cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos = 0
            if cargo_siorg:
                pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
            
            pontos_total = pontos * quantidade
            
            if unidade in unidades_pontos:
                unidades_pontos[unidade]['pontos'] += pontos_total
            else:
                unidades_pontos[unidade] = {
                    'pontos': pontos_total,
                    'sigla_unidade': registro.sigla_unidade
                }
        
        # Segundo, criar dados finais com contagem correta de funcionários
        unidades_dados = {}
        
        # Se há filtro, agrupar tudo sob a unidade filtrada
        if filtro_unidade:
            # Encontrar a unidade principal do filtro
            sigla_upper = filtro_unidade.upper()
            unidade_principal = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla_upper) | 
                Q(sigla__iexact=sigla_upper)
            ).first()
            
            if unidade_principal:
                # CORREÇÃO: Usar APENAS os pontos já calculados corretamente na query filtrada (IGUAL AO IEE)
                # Calcular total de pontos da query filtrada
                total_pontos_filtro = 0
                for registro in query:
                    quantidade = int(registro.quantidade or 0)
                    categoria = int(registro.categoria) if registro.categoria is not None else 1
                    nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
                    
                    cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
                    cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
                    
                    cargo_siorg = None
                    for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                        if key in cargos_siorg_dict:
                            cargo_siorg = cargos_siorg_dict[key]
                            break
                    
                    pontos = 0
                    if cargo_siorg:
                        pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
                    
                    total_pontos_filtro += pontos * quantidade
                
                # Usar a lógica hierárquica para contar funcionários da unidade principal (IGUAL AO IEE)
                colaboradores = contar_funcionarios_unidade(unidade_principal.sigla_unidade)
                
                unidades_dados[unidade_principal.denominacao_unidade] = {
                    'unidade': unidade_principal.denominacao_unidade,
                    'pontos': total_pontos_filtro,
                    'colaboradores': colaboradores
                }
            else:
                # Fallback: usar lógica original se não encontrar a unidade principal
                for unidade, dados_pontos in unidades_pontos.items():
                    sigla_unidade = dados_pontos['sigla_unidade']
                    colaboradores = contar_funcionarios_unidade(sigla_unidade) if sigla_unidade else 0
                    
                    unidades_dados[unidade] = {
                        'unidade': unidade,
                        'pontos': dados_pontos['pontos'],
                        'colaboradores': colaboradores
                    }
        else:
            # Sem filtro: usar lógica original (cada unidade separadamente) - IGUAL AO IEE
            for unidade, dados_pontos in unidades_pontos.items():
                sigla_unidade = dados_pontos['sigla_unidade']
                colaboradores = contar_funcionarios_unidade(sigla_unidade) if sigla_unidade else 0
                
                unidades_dados[unidade] = {
                    'unidade': unidade,
                    'pontos': dados_pontos['pontos'],
                    'colaboradores': colaboradores
                }
        
        # Converter para lista e calcular índices
        tabela_final = []
        for dados in unidades_dados.values():
            if dados['colaboradores'] > 0 or dados['pontos'] > 0:  # Só incluir unidades com dados
                # Calcular IDP: Pontos por colaborador
                if dados['colaboradores'] > 0:
                    dados['idp'] = round(dados['pontos'] / dados['colaboradores'], 2)
                else:
                    dados['idp'] = dados['pontos']  # Se não há colaboradores, IDP = pontos total
                
                dados['pontos'] = round(dados['pontos'], 2)
                tabela_final.append(dados)
        
        # Ordenar por unidade
        tabela_final.sort(key=lambda x: x['unidade'])
        
        # Salvar dados no cache por 30 minutos (1800 segundos)
        cache.set(cache_key, tabela_final, 1800)
        
        # Implementar paginação
        total_registros = len(tabela_final)
        total_pages = (total_registros + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        dados_paginados = tabela_final[start_index:end_index]
        
        return JsonResponse({
            'status': 'success',
            'data': dados_paginados,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_registros': total_registros,
                'has_next': page < total_pages,
                'has_previous': page > 1
            },
            'filtros': {
                'unidade': filtro_unidade,
                'total_registros': total_registros
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar dados IDP: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_relatorio_iee(request):
    """
    API específica para relatório IEE.
    Retorna dados de pontos e colaboradores organizados por unidade para cálculo do IEE.
    """
    try:
        # Parâmetros de filtro e paginação
        filtro_unidade = request.GET.get('unidade', '').strip()
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 11))
        
        # Criar chave de cache única baseada nos filtros
        cache_key = f"iee_data_{filtro_unidade}_{hash(filtro_unidade)}"
        
        # Tentar buscar dados do cache primeiro
        dados_cache = cache.get(cache_key)
        if dados_cache is not None:
            # Dados em cache encontrados - aplicar apenas paginação
            tabela_final = dados_cache
            total_registros = len(tabela_final)
            total_pages = (total_registros + per_page - 1) // per_page
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            dados_paginados = tabela_final[start_index:end_index]
            
            return JsonResponse({
                'status': 'success',
                'data': dados_paginados,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_registros': total_registros,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                },
                'filtros': {
                    'unidade': filtro_unidade,
                    'total_registros': total_registros
                }
            })
        
        # Se não há cache, processar dados completos
        from django.db.models import Q
        from functools import reduce
        import operator
        
        # Consulta base
        query = UnidadeCargo.objects.all()
        
        # Aplicar filtro de unidade com busca hierárquica se fornecido
        if filtro_unidade:
            # Busca hierárquica: encontrar códigos associados à sigla/unidade
            sigla_upper = filtro_unidade.upper()
            codigos_associados = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla_upper) | 
                Q(sigla__iexact=sigla_upper)
            ).values_list('codigo_unidade', flat=True).distinct()
            
            codigos_lista = list(codigos_associados)
            
            if codigos_lista:
                # CORREÇÃO DO FILTRO: usar a mesma lógica do nosso teste que funciona
                filtros_hierarquicos = []
                for code in codigos_lista:
                    # Incluir a própria unidade
                    filtros_hierarquicos.append(Q(codigo_unidade=code))
                    # Incluir subordinadas diretas
                    filtros_hierarquicos.append(Q(grafo__startswith=f"{code}-"))
                    # Incluir descendentes que são filhos (código no final do grafo seguido de -)
                    filtros_hierarquicos.append(Q(grafo__contains=f"-{code}-"))
                
                query = query.filter(reduce(operator.or_, filtros_hierarquicos))
                

            else:
                # Fallback para busca por nome
                query = query.filter(
                    Q(denominacao_unidade__icontains=filtro_unidade) |
                    Q(sigla_unidade__icontains=filtro_unidade)
                )
        
        # Carregar os cargos do SIORG para matching (mesma lógica do Comparador)
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
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao carregar cargos SIORG: {str(e)}")
        
        # Primeiro, agrupar dados por unidade para calcular pontos
        unidades_pontos = {}
        total_pontos_instituicao = 0
        
        for registro in query:
            unidade = registro.denominacao_unidade or registro.sigla_unidade or 'Unidade não identificada'
            quantidade = int(registro.quantidade or 0)
            
            # Calcular pontos usando a mesma lógica do Comparador
            categoria = int(registro.categoria) if registro.categoria is not None else 1
            nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
            
            cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos = 0
            if cargo_siorg:
                pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
            
            pontos_total = pontos * quantidade
            
            if unidade in unidades_pontos:
                unidades_pontos[unidade]['pontos'] += pontos_total
                # Manter referência à sigla da primeira ocorrência
            else:
                unidades_pontos[unidade] = {
                    'pontos': pontos_total,
                    'sigla_unidade': registro.sigla_unidade
                }
            
            total_pontos_instituicao += pontos_total
        
        # Segundo, criar dados finais com contagem correta de funcionários
        unidades_dados = {}
        
        # Se há filtro, agrupar tudo sob a unidade filtrada
        if filtro_unidade:
            # Encontrar a unidade principal do filtro
            sigla_upper = filtro_unidade.upper()
            unidade_principal = UnidadeCargo.objects.filter(
                Q(sigla_unidade__iexact=sigla_upper) | 
                Q(sigla__iexact=sigla_upper)
            ).first()
            
            if unidade_principal:
                # CORREÇÃO: Usar APENAS os pontos já calculados corretamente na query filtrada
                # (não somar novamente, pois a query já foi filtrada)
                total_pontos_filtro = total_pontos_instituicao  # Este já é o total filtrado
                

                
                # Usar a lógica hierárquica para contar funcionários da unidade principal
                colaboradores = contar_funcionarios_unidade(unidade_principal.sigla_unidade)
                
                unidades_dados[unidade_principal.denominacao_unidade] = {
                    'unidade': unidade_principal.denominacao_unidade,
                    'pontos': total_pontos_filtro,
                    'colaboradores': colaboradores
                }
            else:
                # Fallback: usar lógica original se não encontrar a unidade principal
                for unidade, dados_pontos in unidades_pontos.items():
                    sigla_unidade = dados_pontos['sigla_unidade']
                    colaboradores = contar_funcionarios_unidade(sigla_unidade) if sigla_unidade else 0
                    
                    unidades_dados[unidade] = {
                        'unidade': unidade,
                        'pontos': dados_pontos['pontos'],
                        'colaboradores': colaboradores
                    }
        else:
            # Sem filtro: usar lógica original (cada unidade separadamente)
            for unidade, dados_pontos in unidades_pontos.items():
                sigla_unidade = dados_pontos['sigla_unidade']
                colaboradores = contar_funcionarios_unidade(sigla_unidade) if sigla_unidade else 0
                
                unidades_dados[unidade] = {
                    'unidade': unidade,
                    'pontos': dados_pontos['pontos'],
                    'colaboradores': colaboradores
                }
        
        # Calcular total de colaboradores da instituição SEMPRE (não depende do filtro)
        # Contar todos os funcionários válidos da tabela RelatorioGratificacoes
        from .models import RelatorioGratificacoes
        total_colaboradores_instituicao = RelatorioGratificacoes.objects.exclude(
            coordenacao__isnull=True
        ).exclude(
            coordenacao=""
        ).count()
        
        # Calcular total de pontos da instituição SEMPRE (não depende do filtro)
        # Usar todos os registros, não apenas os filtrados
        todos_registros = UnidadeCargo.objects.all()
        total_pontos_instituicao_real = 0
        
        for registro in todos_registros:
            quantidade = int(registro.quantidade or 0)
            categoria = int(registro.categoria) if registro.categoria is not None else 1
            nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
            
            cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos = 0
            if cargo_siorg:
                pontos = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
            
            total_pontos_instituicao_real += pontos * quantidade
        
        # Calcular a média institucional FIXA (nunca muda)
        media_institucional = 0
        if total_colaboradores_instituicao > 0:
            media_institucional = total_pontos_instituicao_real / total_colaboradores_instituicao
        
        # Converter para lista e calcular IEE
        tabela_final = []
        for dados in unidades_dados.values():
            if dados['colaboradores'] > 0 or dados['pontos'] > 0:  # Só incluir unidades com dados
                # Calcular IEE: (Pontos da Unidade / Colaboradores da Unidade) / (Média Institucional)
                if dados['colaboradores'] > 0 and media_institucional > 0:
                    densidade_unidade = dados['pontos'] / dados['colaboradores']
                    dados['iee'] = round(densidade_unidade / media_institucional, 2)
                else:
                    dados['iee'] = 0
                
                dados['pontos'] = round(dados['pontos'], 2)
                tabela_final.append(dados)
        
        # Ordenar por unidade
        tabela_final.sort(key=lambda x: x['unidade'])
        
        # Salvar dados no cache por 30 minutos (1800 segundos)
        cache.set(cache_key, tabela_final, 1800)
        
        # Implementar paginação
        total_registros = len(tabela_final)
        total_pages = (total_registros + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        dados_paginados = tabela_final[start_index:end_index]
        
        return JsonResponse({
            'status': 'success',
            'data': dados_paginados,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_registros': total_registros,
                'has_next': page < total_pages,
                'has_previous': page > 1
            },
                        'filtros': {
                'unidade': filtro_unidade,
                'total_registros': total_registros
            },
            'totais_instituicao': {
                'colaboradores': total_colaboradores_instituicao,
                'pontos': round(total_pontos_instituicao_real, 2),
                'media_institucional': round(media_institucional, 2)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar dados IEE: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_historico_decretos(request):
    """
    API para histórico de decretos.
    """
    from .models import Decreto
    
    try:
        decretos_db = Decreto.objects.all().order_by('-data_publicacao')
        
        decretos = []
        for decreto in decretos_db:
            decretos.append({
                'id': decreto.id,
                'numero': decreto.numero,
                'data': decreto.data_publicacao.strftime('%Y-%m-%d'),
                'titulo': decreto.titulo,
                'tipo': decreto.get_tipo_display(),
                'status': decreto.get_status_display()
            })
        
        # Se não há decretos no banco, usar dados simulados
        if not decretos:
            decretos = [
                {
                    'id': 1,
                    'numero': 'Decreto nº 10.185/2019',
                    'data': '2019-12-20',
                    'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério da Economia',
                    'tipo': 'Estrutura Regimental',
                    'status': 'Vigente'
                },
                {
                    'id': 2,
                    'numero': 'Decreto nº 9.745/2019',
                    'data': '2019-04-08',
                    'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério do Planejamento, Desenvolvimento e Gestão',
                    'tipo': 'Estrutura Regimental',
                    'status': 'Revogado'
                },
                {
                    'id': 3,
                    'numero': 'Decreto nº 11.355/2025',
                    'data': '2025-07-29',
                    'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério do Planejamento e Orçamento',
                    'tipo': 'Estrutura Regimental',
                    'status': 'Vigente'
                }
            ]
        
        return JsonResponse({
            'status': 'success',
            'decretos': decretos
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar decretos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_siglario(request):
    """
    API para o siglário institucional.
    """
    from .models import UnidadeCargo
    
    try:
        # Buscar todas as siglas únicas do organograma
        siglas = UnidadeCargo.objects.values(
            'sigla_unidade', 'denominacao_unidade', 'categoria_unidade'
        ).distinct().exclude(
            sigla_unidade__isnull=True
        ).exclude(
            sigla_unidade__exact=''
        ).order_by('sigla_unidade')
        
        siglario_data = []
        for item in siglas:
            siglario_data.append({
                'sigla': item['sigla_unidade'],
                'denominacao': item['denominacao_unidade'],
                'categoria': item['categoria_unidade'] or 'Não categorizado'
            })
        
        return JsonResponse({
            'status': 'success',
            'data': siglario_data,
            'total': len(siglario_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar siglário: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_unidades_disponiveis(request):
    """
    API para buscar unidades disponíveis para formulários.
    """
    from .models import UnidadeCargo
    
    try:
        unidades = UnidadeCargo.objects.values(
            'denominacao_unidade', 'sigla_unidade'
        ).distinct().exclude(
            denominacao_unidade__isnull=True
        ).exclude(
            denominacao_unidade__exact=''
        ).order_by('denominacao_unidade')
        
        unidades_data = []
        for unidade in unidades:
            unidades_data.append({
                'nome': unidade['denominacao_unidade'],
                'sigla': unidade['sigla_unidade'] or ''
            })
        
        return JsonResponse({
            'status': 'success',
            'unidades': unidades_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar unidades: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_solicitacao_realocacao(request):
    """
    Processa o envio de solicitação de realocação.
    """
    from .models import SolicitacaoRealocacao
    
    try:
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['nome_servidor', 'matricula', 'unidade_atual', 'unidade_destino', 'justificativa']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Campo obrigatório não preenchido: {campo}'
                }, status=400)
        
        # Criar solicitação
        solicitacao = SolicitacaoRealocacao.objects.create(
            nome_servidor=data['nome_servidor'],
            matricula_siape=data['matricula'],
            unidade_atual=data['unidade_atual'],
            unidade_destino=data['unidade_destino'],
            justificativa=data['justificativa'],
            usuario_solicitante=request.user
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Solicitação de realocação enviada com sucesso!',
            'id': solicitacao.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao processar solicitação: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def enviar_solicitacao_permuta(request):
    """
    Processa o envio de solicitação de permuta.
    """
    from .models import SolicitacaoPermuta
    
    try:
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['servidor1', 'matricula1', 'servidor2', 'matricula2']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Campo obrigatório não preenchido: {campo}'
                }, status=400)
        
        # Buscar unidades dos servidores (simplificado - em produção seria mais complexo)
        unidade1 = "Unidade a definir"  # Aqui seria feita uma busca real
        unidade2 = "Unidade a definir"  # Aqui seria feita uma busca real
        
        # Criar solicitação
        solicitacao = SolicitacaoPermuta.objects.create(
            nome_servidor1=data['servidor1'],
            matricula_servidor1=data['matricula1'],
            unidade_servidor1=unidade1,
            nome_servidor2=data['servidor2'],
            matricula_servidor2=data['matricula2'],
            unidade_servidor2=unidade2,
            observacoes=data.get('observacoes', ''),
            usuario_solicitante=request.user
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Solicitação de permuta enviada com sucesso!',
            'id': solicitacao.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao processar solicitação: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_minhas_solicitacoes(request):
    """
    API para listar as solicitações do usuário (realocações e permutas).
    """
    try:
        # Buscar solicitações de realocação
        solicitacoes_realocacao = SolicitacaoRealocacao.objects.filter(
            usuario_solicitante=request.user
        ).order_by('-data_solicitacao')
        
        # Buscar solicitações de permuta
        solicitacoes_permuta = SolicitacaoPermuta.objects.filter(
            usuario_solicitante=request.user
        ).order_by('-data_solicitacao')
        
        # Preparar dados
        realocacoes_data = []
        for sol in solicitacoes_realocacao:
            realocacoes_data.append({
                'id': sol.id,
                'tipo': 'realocacao',
                'nome_servidor': sol.nome_servidor,
                'unidade_atual': sol.unidade_atual,
                'unidade_destino': sol.unidade_destino,
                'status': sol.status,
                'data_solicitacao': sol.data_solicitacao.strftime('%d/%m/%Y %H:%M'),
                'observacoes': sol.observacoes_analise or ''
            })
        
        permutas_data = []
        for sol in solicitacoes_permuta:
            permutas_data.append({
                'id': sol.id,
                'tipo': 'permuta',
                'servidor1': f"{sol.nome_servidor1} ({sol.unidade_servidor1})",
                'servidor2': f"{sol.nome_servidor2} ({sol.unidade_servidor2})",
                'status': sol.status,
                'data_solicitacao': sol.data_solicitacao.strftime('%d/%m/%Y %H:%M'),
                'observacoes': sol.observacoes_analise or ''
            })
        
        return JsonResponse({
            'realocacoes': realocacoes_data,
            'permutas': permutas_data,
            'total': len(realocacoes_data) + len(permutas_data)
        })
        
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


# === NOVAS VIEWS PARA SISTEMA DE TRÊS NÍVEIS DE USUÁRIOS ===

@login_required
@require_http_methods(["GET"])
def listar_simulacoes_gerente(request):
    """
    Lista simulações visíveis para gerentes (enviadas para análise por usuários internos)
    """
    from .models import obter_tipo_usuario
    
    if obter_tipo_usuario(request.user) != 'gerente':
        return JsonResponse({'erro': 'Acesso negado'}, status=403)
    
    # Buscar simulações enviadas para análise e rejeitadas por usuários internos
    simulacoes = SimulacaoSalva.objects.filter(
        status__in=['enviada_analise', 'rejeitada', 'rejeitada_editada'],
        visivel_para_gerentes=True
    ).order_by('-atualizado_em')
    
    data = []
    for sim in simulacoes:
        # Só incluir se o usuário for realmente interno
        if sim.tipo_usuario_atual == 'interno':
            data.append({
                'id': sim.id,
                'nome': sim.nome,
                'descricao': sim.descricao or '',
                'unidade_base': sim.unidade_base or '',
                'usuario': sim.usuario.get_full_name() or sim.usuario.username,
                'usuario_email': sim.usuario.email,
                'status': sim.get_status_display(),
                'tipo_usuario': sim.get_tipo_usuario_display_atual(),
                'criado_em': sim.criado_em.strftime('%d/%m/%Y %H:%M'),
                'atualizado_em': sim.atualizado_em.strftime('%d/%m/%Y %H:%M')
            })
    
        return JsonResponse({
        'simulacoes': data,
        'total': len(data)
    })


@login_required
@require_http_methods(["POST"])
def enviar_simulacao_para_analise(request):
    """
    Envia uma simulação para análise (disponível para usuários internos)
    """
    try:
        data = json.loads(request.body)
        simulacao_id = data.get('simulacao_id')
        
        if not simulacao_id:
            return JsonResponse({'erro': 'ID da simulação é obrigatório'}, status=400)
        
        # Verificar se o usuário é interno (tem permissão para enviar para análise)
        from .models import obter_tipo_usuario
        if obter_tipo_usuario(request.user) != 'interno':
            return JsonResponse({'erro': 'Apenas usuários internos podem enviar simulações para análise'}, status=403)
        
        # Buscar a simulação
        try:
            simulacao = SimulacaoSalva.objects.get(id=simulacao_id, usuario=request.user)
        except SimulacaoSalva.DoesNotExist:
            return JsonResponse({'erro': 'Simulação não encontrada'}, status=404)
        
        # Verificar se está em status válido para envio
        if simulacao.status not in ['rascunho', 'rejeitada', 'rejeitada_editada']:
            return JsonResponse({'erro': 'Esta simulação já foi enviada para análise ou aprovada'}, status=400)
        
        # Atualizar status
        status_anterior = simulacao.status
        simulacao.status = 'enviada_analise'
        simulacao.save()
        
        # Criar notificações para gerentes
        from .models import TipoUsuario
        gerentes = User.objects.filter(tipo_usuario_simulacao__tipo='gerente', tipo_usuario_simulacao__ativo=True)
        for gerente in gerentes:
            if status_anterior in ['rejeitada', 'rejeitada_editada']:
                titulo = f'Simulação corrigida para reavaliação: {simulacao.nome}'
                mensagem = f'{request.user.get_full_name() or request.user.username} corrigiu e reenviou a simulação "{simulacao.nome}" para nova análise.'
            else:
                titulo = f'Nova simulação para análise: {simulacao.nome}'
                mensagem = f'{request.user.get_full_name() or request.user.username} enviou a simulação "{simulacao.nome}" para análise.'
            
            NotificacaoSimulacao.objects.create(
                usuario=gerente,
                tipo='simulacao_enviada',
                titulo=titulo,
                mensagem=mensagem,
                simulacao=simulacao
            )
        
        if status_anterior in ['rejeitada', 'rejeitada_editada']:
            mensagem_sucesso = 'Simulação corrigida e reenviada para análise com sucesso'
        else:
            mensagem_sucesso = 'Simulação enviada para análise com sucesso'
        
        return JsonResponse({
            'mensagem': mensagem_sucesso,
            'status': simulacao.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def avaliar_simulacao(request):
    """
    Permite que gerentes aprovem ou rejeitem simulações
    """
    try:
        from .models import obter_tipo_usuario
        if obter_tipo_usuario(request.user) != 'gerente':
            return JsonResponse({'erro': 'Acesso negado'}, status=403)
        
        data = json.loads(request.body)
        simulacao_id = data.get('simulacao_id')
        acao = data.get('acao')  # 'aprovar' ou 'rejeitar'
        observacoes = data.get('observacoes', '')
        
        if not all([simulacao_id, acao]):
            return JsonResponse({'erro': 'ID da simulação e ação são obrigatórios'}, status=400)
        
        if acao not in ['aprovar', 'rejeitar']:
            return JsonResponse({'erro': 'Ação deve ser "aprovar" ou "rejeitar"'}, status=400)
        
        # Buscar a simulação (pode estar em análise ou rejeitada para reavaliação)
        try:
            simulacao = SimulacaoSalva.objects.get(
                id=simulacao_id, 
                status__in=['enviada_analise', 'rejeitada', 'rejeitada_editada'],
                visivel_para_gerentes=True
            )
        except SimulacaoSalva.DoesNotExist:
            return JsonResponse({'erro': 'Simulação não encontrada ou não disponível para avaliação'}, status=404)
        
        # Atualizar status
        status_anterior = simulacao.status
        if acao == 'aprovar':
            simulacao.status = 'aprovada'
            mensagem_tipo = 'simulacao_aprovada'
            if status_anterior in ['rejeitada', 'rejeitada_editada']:
                mensagem_titulo = f'Simulação reavaliada e aprovada: {simulacao.nome}'
                mensagem_texto = f'Sua simulação "{simulacao.nome}" foi reavaliada e aprovada após as correções.'
            else:
                mensagem_titulo = f'Simulação aprovada: {simulacao.nome}'
                mensagem_texto = f'Sua simulação "{simulacao.nome}" foi aprovada.'
        else:
            simulacao.status = 'rejeitada'
            mensagem_tipo = 'simulacao_rejeitada'
            mensagem_titulo = f'Simulação rejeitada: {simulacao.nome}'
            mensagem_texto = f'Sua simulação "{simulacao.nome}" foi rejeitada. Faça as correções necessárias e solicite nova avaliação.'
        
        if observacoes:
            mensagem_texto += f' Observações: {observacoes}'
        
        simulacao.save()
        
        # Criar notificação para o criador da simulação
        NotificacaoSimulacao.objects.create(
            usuario=simulacao.usuario,
            tipo=mensagem_tipo,
            titulo=mensagem_titulo,
            mensagem=mensagem_texto,
            simulacao=simulacao
        )
        
        return JsonResponse({
            'mensagem': f'Simulação {acao}da com sucesso',
            'status': simulacao.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def criar_solicitacao_simulacao(request):
    """
    Permite que gerentes criem solicitações de simulação para usuários internos
    """
    try:
        from .models import obter_tipo_usuario
        if obter_tipo_usuario(request.user) != 'gerente':
            return JsonResponse({'erro': 'Apenas gerentes podem criar solicitações'}, status=403)
        
        data = json.loads(request.body)
        usuario_designado_id = data.get('usuario_designado_id')
        titulo = data.get('titulo', '').strip()
        descricao = data.get('descricao', '').strip()
        unidade_base_sugerida = data.get('unidade_base_sugerida', '').strip()
        prazo_estimado = data.get('prazo_estimado')
        prioridade = data.get('prioridade', 'normal')
        
        # Validações
        if not all([usuario_designado_id, titulo, descricao]):
            return JsonResponse({'erro': 'Usuário designado, título e descrição são obrigatórios'}, status=400)
        
        # Verificar se o usuário designado existe e é interno
        try:
            usuario_designado = User.objects.get(id=usuario_designado_id)
            if obter_tipo_usuario(usuario_designado) != 'interno':
                return JsonResponse({'erro': 'Usuário designado deve ser um usuário interno'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'erro': 'Usuário designado não encontrado'}, status=404)
        
        # Converter prazo se fornecido
        prazo_obj = None
        if prazo_estimado:
            try:
                from datetime import datetime
                prazo_obj = datetime.strptime(prazo_estimado, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'erro': 'Formato de data inválido para prazo estimado'}, status=400)
        
        # Criar solicitação
        solicitacao = SolicitacaoSimulacao.objects.create(
            solicitante=request.user,
            usuario_designado=usuario_designado,
            titulo=titulo,
            descricao=descricao,
            unidade_base_sugerida=unidade_base_sugerida,
            prazo_estimado=prazo_obj,
            prioridade=prioridade
        )
        
        # Criar notificação para o usuário designado
        NotificacaoSimulacao.objects.create(
            usuario=usuario_designado,
            tipo='nova_solicitacao',
            titulo=f'Nova solicitação de simulação: {titulo}',
            mensagem=f'Você recebeu uma nova solicitação de simulação de {request.user.get_full_name() or request.user.username}.',
            solicitacao=solicitacao
        )
        
        return JsonResponse({
            'mensagem': 'Solicitação criada com sucesso',
            'solicitacao_id': solicitacao.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def listar_usuarios_internos(request):
    """
    Lista usuários internos disponíveis para receber solicitações
    """
    from .models import obter_tipo_usuario, TipoUsuario
    
    if obter_tipo_usuario(request.user) != 'gerente':
        return JsonResponse({'erro': 'Acesso negado'}, status=403)
    
    # Buscar usuários que são internos baseado no modelo TipoUsuario
    usuarios_internos = User.objects.filter(
        tipo_usuario_simulacao__tipo='interno',
        tipo_usuario_simulacao__ativo=True,
        is_active=True
    ).distinct()
    
    data = []
    for usuario in usuarios_internos:
        nome_completo = usuario.get_full_name()
        if not nome_completo or nome_completo.strip() == '':
            nome_completo = usuario.username
            
        data.append({
            'id': usuario.id,
            'username': usuario.username,
            'nome_completo': nome_completo,
            'email': usuario.email or 'Sem email',
            'grupos': [group.name for group in usuario.groups.all()]
        })
    
    return JsonResponse({
        'usuarios': data,
        'total': len(data)
    })


@login_required
@require_http_methods(["GET"])
def minhas_solicitacoes_simulacao(request):
    """
    Lista solicitações de simulação recebidas pelo usuário
    """
    # Buscar solicitações recebidas
    solicitacoes = SolicitacaoSimulacao.objects.filter(
        usuario_designado=request.user
    ).order_by('-criada_em')
    
    data = []
    for sol in solicitacoes:
        data.append({
            'id': sol.id,
            'titulo': sol.titulo,
            'descricao': sol.descricao,
            'solicitante': sol.solicitante.get_full_name() or sol.solicitante.username,
            'solicitante_email': sol.solicitante.email,
            'unidade_base_sugerida': sol.unidade_base_sugerida or '',
            'prazo_estimado': sol.prazo_estimado.strftime('%d/%m/%Y') if sol.prazo_estimado else '',
            'prioridade': sol.get_prioridade_display(),
            'status': sol.get_status_display(),
            'criada_em': sol.criada_em.strftime('%d/%m/%Y %H:%M'),
            'aceita_em': sol.aceita_em.strftime('%d/%m/%Y %H:%M') if sol.aceita_em else '',
            'simulacao_criada_id': sol.simulacao_criada.id if sol.simulacao_criada else None,
            'simulacao_criada_nome': sol.simulacao_criada.nome if sol.simulacao_criada else '',
            'observacoes_usuario': sol.observacoes_usuario or ''
        })
    
    return JsonResponse({
        'solicitacoes': data,
        'total': len(data)
    })


@login_required
@require_http_methods(["POST"])
def aceitar_solicitacao_simulacao(request):
    """
    Permite que usuários aceitem uma solicitação de simulação
    """
    try:
        data = json.loads(request.body)
        solicitacao_id = data.get('solicitacao_id')
        observacoes = data.get('observacoes', '')
        
        if not solicitacao_id:
            return JsonResponse({'erro': 'ID da solicitação é obrigatório'}, status=400)
        
        # Buscar a solicitação
        try:
            solicitacao = SolicitacaoSimulacao.objects.get(
                id=solicitacao_id, 
                usuario_designado=request.user,
                status='pendente'
            )
        except SolicitacaoSimulacao.DoesNotExist:
            return JsonResponse({'erro': 'Solicitação não encontrada ou já foi processada'}, status=404)
        
        # Atualizar solicitação
        solicitacao.status = 'em_andamento'
        solicitacao.aceita_em = timezone.now()
        if observacoes:
            solicitacao.observacoes_usuario = observacoes
        solicitacao.save()
        
        # Criar notificação para o solicitante
        NotificacaoSimulacao.objects.create(
            usuario=solicitacao.solicitante,
            tipo='solicitacao_aceita',
            titulo=f'Solicitação aceita: {solicitacao.titulo}',
            mensagem=f'{request.user.get_full_name() or request.user.username} aceitou sua solicitação de simulação.',
            solicitacao=solicitacao
        )
        
        return JsonResponse({
            'mensagem': 'Solicitação aceita com sucesso',
            'status': solicitacao.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def vincular_simulacao_solicitacao(request):
    """
    Vincula uma simulação criada a uma solicitação
    """
    try:
        data = json.loads(request.body)
        solicitacao_id = data.get('solicitacao_id')
        simulacao_id = data.get('simulacao_id')
        
        if not all([solicitacao_id, simulacao_id]):
            return JsonResponse({'erro': 'ID da solicitação e da simulação são obrigatórios'}, status=400)
        
        # Buscar solicitação e simulação
        try:
            solicitacao = SolicitacaoSimulacao.objects.get(
                id=solicitacao_id,
                usuario_designado=request.user
            )
            simulacao = SimulacaoSalva.objects.get(
                id=simulacao_id,
                usuario=request.user
            )
        except (SolicitacaoSimulacao.DoesNotExist, SimulacaoSalva.DoesNotExist):
            return JsonResponse({'erro': 'Solicitação ou simulação não encontrada'}, status=404)
        
        # Vincular simulação à solicitação
        solicitacao.simulacao_criada = simulacao
        solicitacao.status = 'concluida'
        solicitacao.save()
        
        return JsonResponse({
            'mensagem': 'Simulação vinculada à solicitação com sucesso'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def minhas_notificacoes(request):
    """
    Lista notificações do usuário
    """
    notificacoes = NotificacaoSimulacao.objects.filter(
        usuario=request.user
    ).order_by('-criada_em')[:20]  # Últimas 20 notificações
    
    data = []
    for notif in notificacoes:
        data.append({
            'id': notif.id,
            'tipo': notif.tipo,
            'titulo': notif.titulo,
            'mensagem': notif.mensagem,
            'lida': notif.lida,
            'criada_em': notif.criada_em.strftime('%d/%m/%Y %H:%M'),
            'solicitacao_id': notif.solicitacao.id if notif.solicitacao else None,
            'simulacao_id': notif.simulacao.id if notif.simulacao else None
        })
    
    # Contar não lidas
    nao_lidas = NotificacaoSimulacao.objects.filter(
        usuario=request.user,
        lida=False
    ).count()
    
    return JsonResponse({
        'notificacoes': data,
        'total': len(data),
        'nao_lidas': nao_lidas
    })


@login_required
@require_http_methods(["POST"])
def marcar_notificacao_lida(request):
    """
    Marca uma notificação como lida
    """
    try:
        data = json.loads(request.body)
        notificacao_id = data.get('notificacao_id')
        
        if not notificacao_id:
            return JsonResponse({'erro': 'ID da notificação é obrigatório'}, status=400)
        
        try:
            notificacao = NotificacaoSimulacao.objects.get(
                id=notificacao_id,
                usuario=request.user
            )
            notificacao.lida = True
            notificacao.save()
            
            return JsonResponse({'mensagem': 'Notificação marcada como lida'})
        except NotificacaoSimulacao.DoesNotExist:
            return JsonResponse({'erro': 'Notificação não encontrada'}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def excluir_notificacao(request):
    """
    Exclui uma notificação específica do usuário
    """
    try:
        # Verificar se há dados no corpo da requisição
        if hasattr(request, 'body') and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                notificacao_id = data.get('notificacao_id')
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({'erro': 'Dados JSON inválidos'}, status=400)
        else:
            return JsonResponse({'erro': 'Dados não fornecidos'}, status=400)
        
        if not notificacao_id:
            return JsonResponse({'erro': 'ID da notificação é obrigatório'}, status=400)
        
        try:
            notificacao = NotificacaoSimulacao.objects.get(
                id=notificacao_id,
                usuario=request.user
            )
            notificacao.delete()
            
            return JsonResponse({'mensagem': 'Notificação excluída com sucesso'})
        except NotificacaoSimulacao.DoesNotExist:
            return JsonResponse({'erro': 'Notificação não encontrada'}, status=404)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao excluir notificação: {str(e)}')
        return JsonResponse({'erro': f'Erro interno: {str(e)}'}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def excluir_todas_notificacoes(request):
    """
    Exclui todas as notificações do usuário
    """
    try:
        # Contar quantas notificações serão excluídas
        total_notificacoes = NotificacaoSimulacao.objects.filter(
            usuario=request.user
        ).count()
        
        if total_notificacoes == 0:
            return JsonResponse({'mensagem': 'Nenhuma notificação encontrada para excluir'})
        
        # Excluir todas as notificações do usuário
        NotificacaoSimulacao.objects.filter(
            usuario=request.user
        ).delete()
        
        return JsonResponse({
            'mensagem': f'{total_notificacoes} notificações excluídas com sucesso',
            'total_excluidas': total_notificacoes
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao excluir todas as notificações: {str(e)}')
        return JsonResponse({'erro': f'Erro interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def adicionar_cargo(request):
    """
    Endpoint para adicionar um novo cargo à estrutura.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Obter dados do JSON
        import json
        data = json.loads(request.body)
        
        # Validar campos obrigatórios
        required_fields = ['sigla_unidade', 'tipo_cargo', 'denominacao', 'categoria', 'nivel', 'quantidade']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}'
                }, status=400)
        
        # Obter dados dos campos
        sigla_unidade = data['sigla_unidade'].strip()
        tipo_cargo = data['tipo_cargo'].strip()
        denominacao = data['denominacao'].strip()
        categoria = int(data['categoria'])
        nivel = int(data['nivel'])
        quantidade = int(data['quantidade'])
        
        # Validações específicas
        if categoria < 1 or categoria > 4:
            return JsonResponse({
                'success': False,
                'error': 'Categoria deve estar entre 1 e 4'
            }, status=400)
            
        if nivel < 1 or nivel > 18:
            return JsonResponse({
                'success': False,
                'error': 'Nível deve estar entre 1 e 18'
            }, status=400)
            
        if quantidade < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantidade deve ser pelo menos 1'
            }, status=400)
        
        # Buscar uma unidade existente com a mesma sigla para pegar informações base
        unidade_base = UnidadeCargo.objects.filter(sigla_unidade=sigla_unidade).first()
        
        if not unidade_base:
            return JsonResponse({
                'success': False,
                'error': f'Não foi encontrada unidade com sigla: {sigla_unidade}'
            }, status=400)
        
        # Buscar dados do cargo SIORG para obter pontos e valor
        cargo_siorg = CargoSIORG.objects.filter(
            cargo__icontains=f"{tipo_cargo} {categoria}"
        ).first()
        
        pontos_unitario = 0
        valor_unitario = 0
        if cargo_siorg:
            # Extrair pontos do campo valor (formato: X.XX/Y.YY pts)
            valor_str = cargo_siorg.valor
            if '/' in valor_str and 'pts' in valor_str:
                try:
                    pontos_parte = valor_str.split('/')[1].replace('pts', '').strip()
                    pontos_unitario = float(pontos_parte)
                except:
                    pontos_unitario = 0
            
            valor_unitario = float(cargo_siorg.unitario) if cargo_siorg.unitario else 0
        
        # Calcular valores totais
        pontos_total = pontos_unitario * quantidade
        valor_total = valor_unitario * quantidade
        
        # Gerar um grafo único para o cargo adicionado manualmente
        import uuid
        grafo_unico = f"MANUAL_{sigla_unidade}_{tipo_cargo}_{categoria}_{nivel}_{uuid.uuid4().hex[:8]}"
        
        # Criar o novo cargo ASSOCIADO AO USUÁRIO
        novo_cargo = UnidadeCargo.objects.create(
            nivel_hierarquico=unidade_base.nivel_hierarquico,
            tipo_unidade=unidade_base.tipo_unidade,
            denominacao_unidade=unidade_base.denominacao_unidade,
            codigo_unidade=unidade_base.codigo_unidade,
            sigla_unidade=sigla_unidade,
            categoria_unidade=unidade_base.categoria_unidade,
            orgao_entidade=unidade_base.orgao_entidade,
            tipo_cargo=tipo_cargo,
            denominacao=denominacao,
            categoria=categoria,
            nivel=nivel,
            quantidade=quantidade,
            sigla=sigla_unidade,
            grafo=grafo_unico,
            pontos_total=pontos_total,
            valor_total=valor_total,
            usuario=request.user  # ✅ ASSOCIAR AO USUÁRIO ATUAL
        )
        
        logger.info(f"Novo cargo criado: {novo_cargo.denominacao} (ID: {novo_cargo.id}) por usuário {request.user.username}")
        
        # Retornar dados do cargo criado
        return JsonResponse({
            'success': True,
            'cargo': {
                'id': novo_cargo.id,
                'sigla': novo_cargo.sigla,
                'tipo_cargo': novo_cargo.tipo_cargo,
                'denominacao': novo_cargo.denominacao,
                'categoria': novo_cargo.categoria,
                'nivel': novo_cargo.nivel,
                'quantidade': novo_cargo.quantidade,
                'pontos': pontos_unitario,  # Pontos unitários para o frontend
                'valor_unitario': valor_unitario,  # Valor unitário para o frontend
                'pontos_total': novo_cargo.pontos_total,
                'valor_total': novo_cargo.valor_total,
                'grafo': novo_cargo.grafo,
                'is_manual': True,  # ✅ MARCAR COMO CARGO MANUAL
                'manual_id': novo_cargo.id  # ✅ ID PARA REMOÇÃO
            },
            'message': 'Cargo adicionado com sucesso!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados JSON inválidos'
        }, status=400)
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro de validação: {str(e)}'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar cargo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def mesclar_simulacoes(request):
    """
    API para mesclar múltiplas simulações (disponível apenas para gerentes)
    """
    from .models import obter_tipo_usuario
    
    try:
        # Verificar se o usuário é gerente
        if obter_tipo_usuario(request.user) != 'gerente':
            return JsonResponse({'erro': 'Apenas gerentes podem mesclar simulações'}, status=403)
        
        data = json.loads(request.body)
        simulacoes_ids = data.get('simulacoes_ids', [])
        nome_mesclagem = data.get('nome_mesclagem', '').strip()
        descricao_mesclagem = data.get('descricao_mesclagem', '').strip()
        metodo_mesclagem = data.get('metodo_mesclagem', 'somar')  # 'somar', 'substituir', 'media'
        
        # Validações
        if not simulacoes_ids or len(simulacoes_ids) < 2:
            return JsonResponse({'erro': 'É necessário selecionar pelo menos 2 simulações para mesclar'}, status=400)
        
        if not nome_mesclagem:
            return JsonResponse({'erro': 'Nome da mesclagem é obrigatório'}, status=400)
        
        # Buscar as simulações
        simulacoes = SimulacaoSalva.objects.filter(id__in=simulacoes_ids)
        
        if len(simulacoes) != len(simulacoes_ids):
            return JsonResponse({'erro': 'Uma ou mais simulações não foram encontradas'}, status=404)
        
        # Verificar se já existe uma simulação com o mesmo nome para o usuário
        if SimulacaoSalva.objects.filter(usuario=request.user, nome=nome_mesclagem).exists():
            return JsonResponse({'erro': f'Já existe uma simulação com o nome "{nome_mesclagem}"'}, status=400)
        
        # Mesclar os dados das simulações
        dados_mesclados = []
        unidades_bases = set()
        nomes_simulacoes = []
        
        # Coletar dados de todas as simulações
        for simulacao in simulacoes:
            nomes_simulacoes.append(simulacao.nome)
            if simulacao.unidade_base:
                unidades_bases.add(simulacao.unidade_base)
            
            # Adicionar dados da simulação aos dados mesclados
            for item in simulacao.dados_estrutura:
                dados_mesclados.append(item.copy())
        
        # Aplicar estratégia de mesclagem baseada no método selecionado
        if metodo_mesclagem == 'somar':
            # Agrupar por chave única (denominacao + categoria + nivel) e somar quantidades
            dados_agrupados = {}
            
            for item in dados_mesclados:
                chave = f"{item.get('denominacao', '')}_{item.get('categoria', '')}_{item.get('nivel', '')}"
                
                if chave in dados_agrupados:
                    # Somar quantidades e recalcular pontos
                    dados_agrupados[chave]['quantidade'] += item.get('quantidade', 0)
                    dados_agrupados[chave]['pontos'] = dados_agrupados[chave]['quantidade'] * item.get('valor_unitario', 0)
                else:
                    dados_agrupados[chave] = item.copy()
            
            dados_finais = list(dados_agrupados.values())
            
        elif metodo_mesclagem == 'substituir':
            # A última simulação sobrescreve as anteriores (baseado na ordem dos IDs)
            dados_finais = simulacoes.last().dados_estrutura.copy()
            
        elif metodo_mesclagem == 'media':
            # Calcular média das quantidades para cargos duplicados
            dados_agrupados = {}
            contador_cargos = {}
            
            for item in dados_mesclados:
                chave = f"{item.get('denominacao', '')}_{item.get('categoria', '')}_{item.get('nivel', '')}"
                
                if chave in dados_agrupados:
                    dados_agrupados[chave]['quantidade'] += item.get('quantidade', 0)
                    contador_cargos[chave] += 1
                else:
                    dados_agrupados[chave] = item.copy()
                    contador_cargos[chave] = 1
            
            # Calcular médias
            for chave, item in dados_agrupados.items():
                item['quantidade'] = round(item['quantidade'] / contador_cargos[chave])
                item['pontos'] = item['quantidade'] * item.get('valor_unitario', 0)
            
            dados_finais = list(dados_agrupados.values())
        
        else:
            dados_finais = dados_mesclados
        
        # Determinar unidade base principal
        unidade_base_principal = list(unidades_bases)[0] if unidades_bases else ''
        
        # Criar descrição automática se não fornecida
        if not descricao_mesclagem:
            descricao_mesclagem = f"Mesclagem de {len(simulacoes)} simulações: {', '.join(nomes_simulacoes[:3])}"
            if len(nomes_simulacoes) > 3:
                descricao_mesclagem += f" e mais {len(nomes_simulacoes) - 3} simulações"
            descricao_mesclagem += f". Método: {metodo_mesclagem}."
        
        # Criar nova simulação mesclada
        simulacao_mesclada = SimulacaoSalva.objects.create(
            usuario=request.user,
            nome=nome_mesclagem,
            descricao=descricao_mesclagem,
            dados_estrutura=dados_finais,
            unidade_base=unidade_base_principal,
            status='rascunho'
        )
        
        return JsonResponse({
            'sucesso': True,
            'simulacao_mesclada': {
                'id': simulacao_mesclada.id,
                'nome': simulacao_mesclada.nome,
                'descricao': simulacao_mesclada.descricao,
                'total_registros': len(dados_finais),
                'unidade_base': unidade_base_principal,
                'simulacoes_origem': nomes_simulacoes,
                'metodo_mesclagem': metodo_mesclagem
            },
            'mensagem': f'Simulações mescladas com sucesso! {len(dados_finais)} registros na nova simulação.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao mesclar simulações: {str(e)}")
        return JsonResponse({'erro': f'Erro interno: {str(e)}'}, status=500)


# === VIEWS PARA EXPORTAÇÃO DE RELATÓRIOS EM PDF ===

@login_required
@require_http_methods(["GET"])
def exportar_relatorio_pdf(request, tipo):
    """
    View unificada para exportar relatórios em PDF.
    Tipos suportados: gratificacoes, idp, iee, decretos, siglario
    """
    try:
        # Buscar dados baseado no tipo de relatório
        if tipo == 'gratificacoes':
            dados = buscar_dados_gratificacoes(request)

        elif tipo == 'idp':
            dados = buscar_dados_idp(request)
        elif tipo == 'iee':
            dados = buscar_dados_iee(request)
        elif tipo == 'decretos':
            dados = buscar_dados_decretos(request)
        elif tipo == 'siglario':
            dados = buscar_dados_siglario(request)
        else:
            return JsonResponse({'erro': 'Tipo de relatório não suportado'}, status=400)
        
        # Gerar PDF usando weasyprint
        return gerar_pdf_relatorio(dados, tipo, request.GET.get('unidade', ''))
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao exportar relatório {tipo}: {str(e)}")
        return JsonResponse({'erro': f'Erro ao gerar relatório: {str(e)}'}, status=500)


def buscar_dados_gratificacoes(request):
    """Busca dados para relatório de gratificações"""
    from django.http import QueryDict
    
    # Simular request para API existente
    query_params = QueryDict(mutable=True)
    query_params.update(request.GET)
    query_params['per_page'] = '1000'  # Buscar todos os dados para PDF
    
    # Criar request temporário com atributos necessários
    request_temp = type('Request', (), {
        'GET': query_params, 
        'method': 'GET',
        'user': request.user  # Adicionar usuário do request original
    })()
    response = api_relatorio_pontos_gratificacoes(request_temp)
    
    if hasattr(response, 'content'):
        import json
        return json.loads(response.content.decode('utf-8'))
    return response





def buscar_dados_idp(request):
    """Busca dados para relatório de IDP"""
    from django.http import QueryDict
    
    query_params = QueryDict(mutable=True)
    query_params.update(request.GET)
    query_params['per_page'] = '1000'
    
    request_temp = type('Request', (), {
        'GET': query_params, 
        'method': 'GET',
        'user': request.user
    })()
    response = api_relatorio_idp(request_temp)
    
    if hasattr(response, 'content'):
        import json
        return json.loads(response.content.decode('utf-8'))
    return response


def buscar_dados_iee(request):
    """Busca dados para relatório de IEE"""
    from django.http import QueryDict
    
    query_params = QueryDict(mutable=True)
    query_params.update(request.GET)
    query_params['per_page'] = '1000'
    
    request_temp = type('Request', (), {
        'GET': query_params, 
        'method': 'GET',
        'user': request.user
    })()
    response = api_relatorio_iee(request_temp)
    
    if hasattr(response, 'content'):
        import json
        return json.loads(response.content.decode('utf-8'))
    return response


def buscar_dados_decretos(request):
    """Busca dados para relatório de decretos"""
    # Implementar quando a API estiver pronta
    return {
        'status': 'success',
        'data': [],
        'filtros': {'unidade': request.GET.get('unidade', '')},
        'totais': {'total_registros': 0}
    }


def buscar_dados_siglario(request):
    """Busca dados para siglário"""
    try:
        from .models import UnidadeCargo
        
        filtro = request.GET.get('filtro', '').strip()
        
        # Buscar unidades
        query = UnidadeCargo.objects.all()
        
        if filtro:
            from django.db.models import Q
            query = query.filter(
                Q(sigla_unidade__icontains=filtro) |
                Q(denominacao_unidade__icontains=filtro)
            )
        
        unidades = query.values(
            'sigla_unidade', 'denominacao_unidade', 'codigo_unidade'
        ).distinct().order_by('sigla_unidade')[:1000]
        
        return {
            'status': 'success',
            'data': list(unidades),
            'filtros': {'filtro': filtro},
            'totais': {'total_registros': len(unidades)}
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'data': []
        }


def gerar_pdf_relatorio(dados, tipo, filtro_unidade=''):
    """
    Gera PDF do relatório usando reportlab ou fallback para HTML
    """
    from django.template.loader import render_to_string
    from django.utils import timezone
    
    # Obter nome completo da unidade se filtro for uma sigla
    nome_unidade_completo = obter_nome_completo_unidade(filtro_unidade) if filtro_unidade else ''
    
    # Configurar timezone do Brasil (Brasília)
    import pytz
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    agora_brasilia = timezone.now().astimezone(fuso_brasilia)
    
    # Preparar contexto para o template
    context = {
        'dados': dados.get('data', []),
        'tipo': tipo,
        'filtro_unidade': filtro_unidade,
        'nome_unidade_completo': nome_unidade_completo,
        'filtros': dados.get('filtros', {}),
        'totais': dados.get('totais', {}),
        'titulo': obter_titulo_relatorio(tipo),
        'data_geracao': agora_brasilia.strftime('%d/%m/%Y %H:%M')
    }
    
    # Preparar filename
    filtro_str = f"_{filtro_unidade}" if filtro_unidade else ""
    
    # Tentar reportlab primeiro (OBRIGATÓRIO para PDF)
    try:
        return gerar_pdf_com_reportlab(dados, tipo, filtro_unidade, context)
    except ImportError as e:
        # Reportlab não instalado - instruir instalação
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"ReportLab não instalado: {str(e)}")
        
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="instalar_reportlab.txt"'
        response.write(f'''ERRO: Biblioteca ReportLab não encontrada!

Para gerar PDFs, execute o comando:

    pip install reportlab

Depois tente exportar novamente.

Erro técnico: {str(e)}
''')
        return response
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao gerar PDF com reportlab: {str(e)}")
        
        # Último recurso: arquivo de erro com instruções
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="erro_pdf_{tipo}.txt"'
        response.write(f'''ERRO ao gerar PDF do relatório {tipo}!

Erro técnico: {str(e)}

Soluções:
1. Verifique se reportlab está instalado: pip install reportlab
2. Entre em contato com o suporte técnico
3. Tente novamente em alguns minutos

Dados do erro:
- Tipo: {tipo}
- Filtro: {filtro_unidade}
- Registros: {len(dados.get('data', []))}
''')
        return response


def gerar_pdf_com_reportlab(dados, tipo, filtro_unidade, context):
    """
    Gera PDF usando reportlab (melhor compatibilidade Windows)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Criar buffer para o PDF
    buffer = BytesIO()
    
    # Criar documento
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.HexColor('#2c5282')
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#718096')
    )
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=10,
        alignment=1,  # Center
        textColor=colors.HexColor('#718096')
    )
    
    # Elementos do documento
    elements = []
    
    # Título (sem informações de filtro)
    titulo = context['titulo']
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 30))
    
    # Remover seção de filtro - não é necessária no PDF
    
    # Tabela de dados
    if context.get('dados'):
        table_data = criar_tabela_dados_reportlab(context['dados'], tipo)
        
        if table_data:
            # Definir larguras das colunas bem espaçadas
            if tipo == 'gratificacoes':
                col_widths = [2.5*inch, 1.0*inch, 1.0*inch, 0.8*inch, 0.8*inch]  # Unidade, Pontos, GSISTE/GSISP, NS, NI
            elif tipo == 'iee':
                col_widths = [1.3*inch, 1.2*inch, 1.3*inch, 1.0*inch, 1.4*inch]  # Unidade(sigla), Pontos, Colaboradores, IEE, Status
            elif tipo == 'idp':
                col_widths = [1.3*inch, 1.2*inch, 1.3*inch, 1.0*inch, 1.4*inch]  # Unidade(sigla), Pontos, Colaboradores, IDP, Classificação
            elif tipo == 'siglario':
                col_widths = [1.5*inch, 1.3*inch, 4.7*inch]  # Sigla, Código, Denominação
            else:
                col_widths = None
            
            table = Table(table_data, colWidths=col_widths)
            
            # Estilo da tabela com melhor espaçamento
            table_style = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
                ('TOPPADDING', (0, 0), (-1, 0), 15),
                ('LEFTPADDING', (0, 0), (-1, 0), 8),
                ('RIGHTPADDING', (0, 0), (-1, 0), 8),
                
                # Dados
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 1), (-1, -1), 8),
                ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                
                # Zebra stripes
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
            ])
            
            # Alinhamento específico por coluna
            if tipo in ['gratificacoes', 'iee', 'idp']:
                # Primeira coluna (Unidade) à esquerda
                table_style.add('ALIGN', (0, 0), (0, -1), 'LEFT')
                # Demais colunas (números) à direita
                for col in range(1, len(table_data[0])):
                    table_style.add('ALIGN', (col, 0), (col, -1), 'RIGHT')
            elif tipo == 'siglario':
                # Todas as colunas à esquerda para siglário
                table_style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
                # Código centralizado
                table_style.add('ALIGN', (1, 0), (1, -1), 'CENTER')
            
            table.setStyle(table_style)
            elements.append(table)
    else:
        elements.append(Paragraph("Nenhum dado encontrado para os critérios selecionados.", styles['Normal']))
    
    # Adicionar "Gerado em:" no final com fonte menor
    elements.append(Spacer(1, 20))
    data_text = f"Gerado em: {context['data_geracao']}"
    if context.get('totais', {}).get('total_registros'):
        data_text += f" | Total de registros: {context['totais']['total_registros']}"
    elements.append(Paragraph(data_text, footer_style))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Preparar resposta
    filtro_str = f"_{filtro_unidade}" if filtro_unidade else ""
    filename = f"relatorio_{tipo}{filtro_str}.pdf"
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    buffer.close()
    
    return response


def extrair_sigla_unidade(nome_unidade):
    """
    Extrai a sigla da unidade (última palavra entre parênteses ou após hífen)
    Exemplos: 
    'Assessoria Especial de Assuntos Parlamentares e Federativos - ASPAF' -> 'ASPAF'
    'Consultoria Jurídica - CONJUR' -> 'CONJUR'
    'Cerimônial - CERIMONIAL' -> 'CERIMONIAL'
    """
    if not nome_unidade or nome_unidade == '-':
        return nome_unidade
    
    # Procurar por sigla entre parênteses no final
    import re
    sigla_parenteses = re.search(r'\(([A-Z]+)\)$', nome_unidade.strip())
    if sigla_parenteses:
        return sigla_parenteses.group(1)
    
    # Procurar por sigla após hífen
    if ' - ' in nome_unidade:
        partes = nome_unidade.split(' - ')
        sigla_candidata = partes[-1].strip()
        # Verificar se é uma sigla (só maiúsculas/números)
        if re.match(r'^[A-Z0-9]+$', sigla_candidata):
            return sigla_candidata
    
    # Se não encontrou sigla específica, pegar a última palavra
    palavras = nome_unidade.strip().split()
    if palavras:
        ultima_palavra = palavras[-1]
        # Remove pontuação
        ultima_palavra = re.sub(r'[^\w]', '', ultima_palavra)
        return ultima_palavra.upper()
    
    return nome_unidade


def criar_tabela_dados_reportlab(dados, tipo):
    """
    Cria dados da tabela formatados para reportlab com quebra de linha automática
    """
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph
    
    styles = getSampleStyleSheet()
    # Estilo para células com quebra de linha
    cell_style = styles['Normal']
    cell_style.fontSize = 9
    cell_style.leading = 11
    
    if tipo == 'gratificacoes':
        headers = ['Unidade', 'Pontos', 'GSISTE/GSISP', 'NS', 'NI']
        rows = [headers]
        for item in dados:
            unidade_nome = str(item.get('unidade', '-'))
            # Extrair só a sigla da unidade
            sigla_unidade = extrair_sigla_unidade(unidade_nome)
            
            row = [
                sigla_unidade,
                f"{item.get('pontos', 0):.2f}",
                f"{item.get('gsist', 0) + item.get('gsisp', 0)}",
                f"{item.get('ns', 0):.2f}",
                f"{item.get('ni', 0):.2f}"
            ]
            rows.append(row)
    

    
    elif tipo == 'iee':
        headers = ['Unidade', 'Pontos', 'Colaboradores', 'IEE', 'Status']
        rows = [headers]
        for item in dados:
            unidade_nome = str(item.get('unidade', '-'))
            # Extrair só a sigla da unidade
            sigla_unidade = extrair_sigla_unidade(unidade_nome)
            
            # Calcular status baseado no IEE
            iee_valor = float(item.get('iee', 0))
            if iee_valor > 1:
                status = 'Acima da Média'
            elif iee_valor == 1:
                status = 'Na Média'
            else:
                status = 'Abaixo da Média'
            
            row = [
                sigla_unidade,
                f"{item.get('pontos', 0):.2f}",
                str(item.get('colaboradores', 0)),
                f"{item.get('iee', 0):.2f}",
                status
            ]
            rows.append(row)
    
    elif tipo == 'idp':
        headers = ['Unidade', 'Pontos', 'Colaboradores', 'IDP', 'Classificação']
        rows = [headers]
        
        # Ordenar dados por IDP (maior para menor) para classificação
        dados_ordenados = sorted(dados, key=lambda x: float(x.get('idp', 0)), reverse=True)
        total_itens = len(dados_ordenados)
        
        for index, item in enumerate(dados_ordenados):
            unidade_nome = str(item.get('unidade', '-'))
            # Extrair só a sigla da unidade
            sigla_unidade = extrair_sigla_unidade(unidade_nome)
            
            # Calcular classificação baseada na posição (terços)
            if index < total_itens / 3:
                classificacao = 'Alta Densidade'
            elif index < (2 * total_itens) / 3:
                classificacao = 'Densidade Média'
            else:
                classificacao = 'Baixa Densidade'
            
            row = [
                sigla_unidade,
                f"{item.get('pontos', 0):.2f}",
                str(item.get('colaboradores', 0)),
                f"{item.get('idp', 0):.2f}",
                classificacao
            ]
            rows.append(row)
    
    elif tipo == 'siglario':
        headers = ['Sigla', 'Código', 'Denominação']
        rows = [headers]
        for item in dados:
            denominacao_nome = str(item.get('denominacao_unidade', '-'))
            # Usar Paragraph para quebra automática na denominação
            denominacao_paragraph = Paragraph(denominacao_nome, cell_style)
            
            row = [
                str(item.get('sigla_unidade', '-')),
                str(item.get('codigo_unidade', '-')),
                denominacao_paragraph
            ]
            rows.append(row)
    
    else:
        return None
    
    return rows


def obter_nome_completo_unidade(sigla_filtro):
    """
    Busca o nome completo da unidade baseado na sigla do filtro
    """
    if not sigla_filtro:
        return ''
    
    try:
        from .models import UnidadeCargo
        from django.db.models import Q
        
        # Buscar unidade pela sigla (case insensitive)
        unidade = UnidadeCargo.objects.filter(
            Q(sigla_unidade__iexact=sigla_filtro) |
            Q(sigla__iexact=sigla_filtro)
        ).first()
        
        if unidade and unidade.denominacao_unidade:
            return unidade.denominacao_unidade
        
        # Se não encontrou, retornar a sigla em maiúsculo
        return sigla_filtro.upper()
        
    except Exception:
        return sigla_filtro.upper()


def obter_titulo_relatorio(tipo):
    """Retorna título do relatório baseado no tipo"""
    titulos = {
        'gratificacoes': 'Relatório de Pontos e Gratificações',

        'idp': 'Relatório de Índice de Densidade de Pessoal',
        'iee': 'Relatório de Índice de Eficiência por Estrutura',
        'decretos': 'Relatório de Decretos',
        'siglario': 'Siglário Institucional'
    }
    return titulos.get(tipo, f'Relatório {tipo.title()}')


def limpar_cache_relatorios():
    """
    Limpa o cache de todos os relatórios.
    Útil para forçar recálculo quando os dados mudam.
    """
    # Limpar cache de gratificações
    cache.delete_pattern("gratificacoes_data_*")
    # Limpar cache de IDP
    cache.delete_pattern("idp_data_*")
    # Limpar cache de IEE
    cache.delete_pattern("iee_data_*")
