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
    Adaptador personalizado para proporcionar uma experiência de login social fluida:
    1. Reconhecer usuários que já se cadastraram anteriormente
    2. Conectar contas sociais a usuários existentes com o mesmo email
    3. Criar automaticamente uma conta com os dados do provedor social para novos usuários
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invocado logo após um login social bem-sucedido,
        mas antes do login ser realmente processado.
        """
        # Se o usuário já está autenticado, não faça nada
        if request.user.is_authenticated:
            return

        # Obter dados importantes
        email = user_email(sociallogin.user)
        provider = sociallogin.account.provider
        uid = sociallogin.account.uid
        
        # Se já existe um usuário com essa conta social, simplesmente conecte-o
        if sociallogin.is_existing:
            return
            
        # Verificar se já existe um usuário com o mesmo email no sistema
        if email:
            # Caso 1: Email já está verificado no sistema
            try:
                # Verificar se já existe um endereço de email verificado no sistema
                existing_email = EmailAddress.objects.get(email__iexact=email, verified=True)
                if existing_email:
                    # Conectar esta conta social ao usuário existente
                    user = existing_email.user
                    sociallogin.connect(request, user)
                    # Fazer login imediatamente
                    sociallogin.user = user
                    auth_login(request, user, 'django.contrib.auth.backends.ModelBackend')
                    # Redirecionar para a página inicial
                    raise ImmediateHttpResponse(redirect('home'))
            except EmailAddress.DoesNotExist:
                pass
            
            # Caso 2: Existe um usuário com mesmo email, mas não verificado
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
                # Se não caiu no caso 1 e encontramos um usuário com mesmo email
                # Vamos conectar a conta social a este usuário
                sociallogin.connect(request, user)
                # Fazer login imediatamente
                sociallogin.user = user
                auth_login(request, user, 'django.contrib.auth.backends.ModelBackend')
                # Marcar email como verificado
                EmailAddress.objects.get_or_create(user=user, email=email,
                                              defaults={'verified': True, 'primary': True})
                # Redirecionar para a página inicial
                raise ImmediateHttpResponse(redirect('home'))
            except User.DoesNotExist:
                pass
            
        # Se chegamos aqui, é um novo usuário social
        # Vamos criar automaticamente uma conta
        user = sociallogin.user
        
        # Garantir que temos um nome de usuário válido e único
        if not user_username(user):
            if email:
                base_username = email.split("@")[0]
                # Verificar se o nome de usuário já existe
                User = get_user_model()
                username = base_username
                counter = 1
                
                # Se o nome de usuário já existe, adicionar um sufixo numérico
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user_username(user, username)
            else:
                # Gerar um nome de usuário aleatório se não houver email
                user_username(user, f"user_{uuid.uuid4().hex[:10]}")

        # Salvar o usuário
        sociallogin.connect(request, user)
        
        # Se temos um email, marcar como verificado automaticamente
        if email:
            EmailAddress.objects.get_or_create(user=user, email=email,
                                           defaults={'verified': True, 'primary': True})

        # Redirecionar para a página inicial
        # Isso impede que o fluxo normal acesse a tela de signup
        return redirect("home")
