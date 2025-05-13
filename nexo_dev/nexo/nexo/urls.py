from django.urls import path, include
from django.contrib import admin
from .views import CustomLoginView, RegisterView, LogoutView, financeira_page, financeira_data, financeira_export, organograma, organograma_data, atualizar_organograma_json

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('financeira/', financeira_page, name='financeira'),
    path('financeira/data/', financeira_data, name='financeira_data'),
    path('financeira/exportar/<str:formato>/', financeira_export, name='financeira_export'),
    path('organograma/', organograma, name='organograma'),
    path('organograma/data/', organograma_data, name='organograma_data'),
    path('atualizar-organograma-json/', atualizar_organograma_json, name='atualizar_organograma_json'),
] 