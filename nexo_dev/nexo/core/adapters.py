from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_username, user_field
from django.shortcuts import redirect
from django.urls import reverse
import uuid
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import login as auth_login
from allauth.socialaccount.models import SocialAccount


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptador personalizado para autenticação social que garante:
    1. Que cada usuário tenha um nome de usuário único
    2. Associação de contas sociais a usuários existentes com o mesmo email
    3. Redirecionamento direto para a página principal após login
    """

    def populate_user(self, request, sociallogin, data):
        """
        Preencher dados do usuário a partir dos dados do provedor social
        Garantir que o usuário tenha um nome de usuário válido
        """
        user = super().populate_user(request, sociallogin, data)

        # Garantir que temos um nome de usuário válido
        if not user.username or user.username == "":
            email = user_email(user)
            if email:
                # Usar a parte do email antes do @ como base para username
                base_username = email.split("@")[0]

                # Verificar se este username já existe
                User = get_user_model()
                username = base_username
                counter = 1

                # Se o username já existe, adicionar um sufixo numérico
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                # Definir o nome de usuário
                user.username = username
            else:
                # Gerar um nome de usuário único com UUID
                user.username = f"user_{uuid.uuid4().hex[:10]}"

        return user

    def pre_social_login(self, request, sociallogin):
        """
        Executado antes de finalizar o login social
        Verificar se existe usuário com mesmo email e conectar a conta social
        """
        # Se o usuário já está autenticado, não fazer nada
        if request.user.is_authenticated:
            return

        # Se a conta social já está conectada a um usuário, deixar o fluxo padrão
        if sociallogin.is_existing:
            return

        # Verificar se existe um usuário com o mesmo email
        email = user_email(sociallogin.user)
        if email:
            try:
                # Verificar se já existe um email verificado no sistema
                existing_email = EmailAddress.objects.get(
                    email__iexact=email, verified=True
                )
                if existing_email:
                    # Redirecionar para página principal após conectar conta
                    user = existing_email.user
                    sociallogin.user = user
                    sociallogin.save(request)
                    auth_login(request, user)
                    raise ImmediateHttpResponse(redirect("home"))
            except EmailAddress.DoesNotExist:
                # Verificar se existe um usuário com o mesmo email, mesmo sem verificação
                User = get_user_model()
                try:
                    user = User.objects.get(email__iexact=email)
                    sociallogin.user = user
                    sociallogin.save(request)
                    # Marcar email como verificado
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=email,
                        defaults={"verified": True, "primary": True},
                    )
                    auth_login(request, user)
                    raise ImmediateHttpResponse(redirect("home"))
                except User.DoesNotExist:
                    pass

        # Garantir que o usuário tenha um nome de usuário válido
        user = sociallogin.user
        if not user.username or user.username == "":
            if email:
                base = email.split("@")[0]
                User = get_user_model()
                username = base
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base}_{counter}"
                    counter += 1
                user.username = username
            else:
                user.username = f"user_{uuid.uuid4().hex[:10]}"
