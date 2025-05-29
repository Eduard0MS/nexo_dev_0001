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
    BaixarAnexoSimulacaoView
)

# app_name = 'core' # Removing app_name to resolve NoReverseMatch with non-namespaced include

urlpatterns = [
    path('', views.home, name='pagina_inicial'), # Corrected to use views.home
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/alterar-senha/', views.alterar_senha, name='alterar_senha'),
    path('organograma/', views.organograma, name='organograma'),
    path('organograma/view/', views.organograma_view, name='organograma_view'),
    path('simular-troca-cargo/', views.simular_troca_cargo, name='simular_troca_cargo'),
    path('api/organograma/', views.api_organograma, name='api_organograma'),
    path('api/organograma/teste/', views.teste_api_organograma, name='teste_api_organograma'),
    path('dashboard/', views.index, name='dashboard'),
    path('api/unidade/<str:codigo_unidade>/', views.get_unidade_data, name='api_unidade_data'),
    path('api/organograma/detalhes/<str:codigo>/', views.api_organograma_detalhes, name='api_organograma_detalhes'),
    path('atualizar-organograma-json/', views.atualizar_organograma_json, name='atualizar_organograma_json'),
    path('api/organograma-filter/', views.api_organograma_filter, name='api_organograma_filter'),
    path('api/cargos_diretos/', views.api_cargos_diretos, name='api_cargos_diretos'),
    path('simulador/', views.comparador, name='simulador'), # Corrected to use views.comparador
    path('comparador/', views.simulacao_page, name='comparador'), # Corrected to use views.simulacao_page
    # path('painel_de_bordo/', PainelDeBordoView.as_view(), name='painel_de_bordo'), # Commented out as PainelDeBordoView is not defined in views.py
    path('financeira/', views.financeira, name='financeira'),
    path('api/financeira-data/', views.financeira_data_real, name='financeira_data'),
    path('api/financeira-organograma/', views.api_financeira_organograma, name='api_financeira_organograma'),
    # path('api/salvar_estruturas/', SalvarEstruturasView.as_view(), name='salvar_estruturas'), # Commenting out
    # path('api/carregar_estruturas/', CarregarEstruturasView.as_view(), name='carregar_estruturas'), # Commenting out
    # path('api/deletar_estrutura/<int:pk>/', DeletarEstruturaView.as_view(), name='deletar_estrutura'), # Commenting out
    # path('api/limpar_estruturas/', LimparEstruturasView.as_view(), name='limpar_estruturas'), # Commenting out
    # path('api/estruturas_salvas/', EstruturasSalvasView.as_view(), name='estruturas_salvas'), # Commenting out
    path('api/baixar_anexo_simulacao/', BaixarAnexoSimulacaoView.as_view(), name='baixar_anexo_simulacao'),
]