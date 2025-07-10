from django.urls import path
from . import views
from .views import (
    # Function-based views that were previously aliased or have specific names
    # PaginaInicialView -> views.home
    # ComparadorView -> views.simulacao_page (for /comparador/ path)
    # SimuladorView -> views.comparador (for /simulador/ path)
    # PainelDeBordoView seems to be missing a definition in views.py
    # SalvarEstruturasView, # Commenting out as it causes ImportError
    # CarregarEstruturasView, # Commenting out
    # DeletarEstruturaView,  # Commenting out
    # LimparEstruturasView,  # Commenting out
    # EstruturasSalvasView, # Commenting out
    BaixarAnexoSimulacaoView,
)

# app_name = 'core' # Removing app_name to resolve NoReverseMatch with non-namespaced include

urlpatterns = [
    path("", views.home, name="pagina_inicial"),  # Corrected to use views.home
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path("perfil/alterar-senha/", views.alterar_senha, name="alterar_senha"),
    path("organograma/", views.organograma, name="organograma"),
    path("organograma/view/", views.organograma_view, name="organograma_view"),
    path("simular-troca-cargo/", views.simular_troca_cargo, name="simular_troca_cargo"),
    path("api/organograma/", views.api_organograma, name="api_organograma"),
    path(
        "api/organograma/teste/",
        views.teste_api_organograma,
        name="teste_api_organograma",
    ),
    path("dashboard/", views.index, name="dashboard"),
    path(
        "api/unidade/<str:codigo_unidade>/",
        views.get_unidade_data,
        name="api_unidade_data",
    ),
    path(
        "api/organograma/detalhes/<str:codigo>/",
        views.api_organograma_detalhes,
        name="api_organograma_detalhes",
    ),
    path(
        "atualizar-organograma-json/",
        views.atualizar_organograma_json,
        name="atualizar_organograma_json",
    ),
    path(
        "api/organograma-filter/",
        views.api_organograma_filter,
        name="api_organograma_filter",
    ),
    path("api/cargos_diretos/", views.api_cargos_diretos, name="api_cargos_diretos"),
    path("api/adicionar-cargo/", views.adicionar_cargo, name="api_adicionar_cargo"),
    path(
        "simulador/", views.comparador, name="simulador"
    ),  # Corrected to use views.comparador
    path(
        "comparador/", views.simulacao_page, name="comparador"
    ),  # Corrected to use views.simulacao_page
    # path('painel_de_bordo/', PainelDeBordoView.as_view(), name='painel_de_bordo'), # Commented out as PainelDeBordoView is not defined in views.py
    path("financeira/", views.financeira, name="financeira"),
    path("api/financeira-data/", views.financeira_data_real, name="financeira_data"),
    path(
        "api/financeira-organograma/",
        views.api_financeira_organograma,
        name="api_financeira_organograma",
    ),
    # path('api/salvar_estruturas/', SalvarEstruturasView.as_view(), name='salvar_estruturas'), # Commenting out
    # path('api/carregar_estruturas/', CarregarEstruturasView.as_view(), name='carregar_estruturas'), # Commenting out
    # path('api/deletar_estrutura/<int:pk>/', DeletarEstruturaView.as_view(), name='deletar_estrutura'), # Commenting out
    # path('api/limpar_estruturas/', LimparEstruturasView.as_view(), name='limpar_estruturas'), # Commenting out
    # path('api/estruturas_salvas/', EstruturasSalvasView.as_view(), name='estruturas_salvas'), # Commenting out
    path(
        "api/baixar_anexo_simulacao/",
        BaixarAnexoSimulacaoView.as_view(),
        name="baixar_anexo_simulacao",
    ),
    # APIs de Simulações Salvas
    path("api/simulacoes/", views.listar_simulacoes, name="listar_simulacoes"),
    path("api/simulacoes/salvar/", views.salvar_simulacao, name="salvar_simulacao"),
    path(
        "api/simulacoes/mesclar/", views.mesclar_simulacoes, name="mesclar_simulacoes"
    ),
    path(
        "api/simulacoes/<int:simulacao_id>/",
        views.carregar_simulacao,
        name="carregar_simulacao",
    ),
    path(
        "api/simulacoes/<int:simulacao_id>/atualizar/",
        views.atualizar_simulacao,
        name="atualizar_simulacao",
    ),
    path(
        "api/simulacoes/<int:simulacao_id>/deletar/",
        views.deletar_simulacao,
        name="deletar_simulacao",
    ),
    # URLs para Sistema de Relatórios
    path("relatorios/", views.relatorios, name="relatorios"),
    path(
        "api/relatorio/pontos-gratificacoes/",
        views.api_relatorio_pontos_gratificacoes,
        name="api_relatorio_pontos_gratificacoes",
    ),
    path(
        "api/relatorio/dimensionamento/",
        views.api_relatorio_dimensionamento,
        name="api_relatorio_dimensionamento",
    ),
    path(
        "api/historico-decretos/",
        views.api_historico_decretos,
        name="api_historico_decretos",
    ),
    path("api/siglario/", views.api_siglario, name="api_siglario"),
    path(
        "api/unidades-disponiveis/",
        views.api_unidades_disponiveis,
        name="api_unidades_disponiveis",
    ),
    path(
        "api/solicitacao-realocacao/",
        views.enviar_solicitacao_realocacao,
        name="enviar_solicitacao_realocacao",
    ),
    path(
        "api/solicitacao-permuta/",
        views.enviar_solicitacao_permuta,
        name="enviar_solicitacao_permuta",
    ),
    path(
        "api/minhas-solicitacoes/",
        views.api_minhas_solicitacoes,
        name="api_minhas_solicitacoes",
    ),
    # URLs para Sistema de Três Níveis de Usuários - Simulações
    path(
        "api/simulacoes/gerente/",
        views.listar_simulacoes_gerente,
        name="listar_simulacoes_gerente",
    ),
    path(
        "api/simulacoes/enviar-analise/",
        views.enviar_simulacao_para_analise,
        name="enviar_simulacao_para_analise",
    ),
    path("api/simulacoes/avaliar/", views.avaliar_simulacao, name="avaliar_simulacao"),
    # URLs para Solicitações de Simulação
    path(
        "api/solicitacoes-simulacao/criar/",
        views.criar_solicitacao_simulacao,
        name="criar_solicitacao_simulacao",
    ),
    path(
        "api/solicitacoes-simulacao/minhas/",
        views.minhas_solicitacoes_simulacao,
        name="minhas_solicitacoes_simulacao",
    ),
    path(
        "api/solicitacoes-simulacao/aceitar/",
        views.aceitar_solicitacao_simulacao,
        name="aceitar_solicitacao_simulacao",
    ),
    path(
        "api/solicitacoes-simulacao/vincular/",
        views.vincular_simulacao_solicitacao,
        name="vincular_simulacao_solicitacao",
    ),
    # URLs para Usuários e Notificações
    path(
        "api/usuarios-internos/",
        views.listar_usuarios_internos,
        name="listar_usuarios_internos",
    ),
    path("api/notificacoes/", views.minhas_notificacoes, name="minhas_notificacoes"),
    path(
        "api/notificacoes/marcar-lida/",
        views.marcar_notificacao_lida,
        name="marcar_notificacao_lida",
    ),
    path(
        "api/notificacoes/excluir/",
        views.excluir_notificacao,
        name="excluir_notificacao",
    ),
    path(
        "api/notificacoes/excluir-todas/",
        views.excluir_todas_notificacoes,
        name="excluir_todas_notificacoes",
    ),
]
