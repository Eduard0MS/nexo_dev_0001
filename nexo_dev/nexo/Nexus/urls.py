from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

from core.views import (
    CustomLoginView,
    register,
    home,
    simulacao_page,
    financeira_page,
    financeira_data,
    financeira_export,
    CustomSocialLoginView,
)

def favicon_view(request):
    """Retorna um favicon SVG simples para evitar erro 404"""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" fill="#4A90E2" rx="4"/>
  <text x="16" y="22" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="middle">N</text>
</svg>'''
    return HttpResponse(svg_content, content_type="image/svg+xml")

urlpatterns = [
    path("admin/", admin.site.urls),
    # Login e logout
    path("login_direct/", CustomLoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="/login_direct/"),
        name="logout",
    ),
    path("accounts/", include("allauth.urls")),  # Rotas do Allauth
    path(
        "accounts/social/signup/",
        CustomSocialLoginView.as_view(),
        name="socialaccount_signup",
    ),
    path("register/", register, name="register"),  # Rota de registro que redireciona para login
    path("home/", home, name="home"),
    path("simulacao/", simulacao_page, name="simulacao"),
    path("financeira/", financeira_page, name="financeira"),
    path("financeira/data/", financeira_data, name="financeira_data"),
    path("financeira/export/", financeira_export, name="financeira_export"),
    # Favicon para evitar erro 404
    path("favicon.ico", favicon_view, name="favicon"),
    # Incluir URLs do app 'core' - DEVE VIR POR ÚLTIMO
    path("", include("core.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else []
