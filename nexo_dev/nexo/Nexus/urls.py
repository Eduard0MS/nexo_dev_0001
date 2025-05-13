from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

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
    path("register/", register, name="register"),
    path("home/", home, name="home"),
    path("simulacao/", simulacao_page, name="simulacao"),
    path("financeira/", financeira_page, name="financeira"),
    path("financeira/data/", financeira_data, name="financeira_data"),
    path("financeira/export/", financeira_export, name="financeira_export"),
    # Incluir URLs do app 'core'
    path("", include("core.urls")),
    # Rota raíz -> envia para login_direct
    path("", RedirectView.as_view(url="/login_direct/", permanent=False), name="root"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else []
