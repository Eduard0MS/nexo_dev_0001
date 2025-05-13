from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='pagina_inicial'),
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
    path('simulador/', views.comparador, name='simulador'),
    path('comparador/', views.simulacao_page, name='comparador'),
    path('financeira/', views.financeira, name='financeira'),
    path('api/financeira-data/', views.financeira_data_real, name='financeira_data'),
    path('api/financeira-organograma/', views.api_financeira_organograma, name='api_financeira_organograma'),
]