from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Limpa todos os dados de autenticação do usuário"

    def handle(self, *args, **kwargs):
        # Remove contas sociais
        SocialToken.objects.all().delete()
        SocialAccount.objects.all().delete()

        # Remove endereços de e-mail
        EmailAddress.objects.all().delete()

        # Remove usuários (exceto superuser)
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(
            self.style.SUCCESS("Dados de autenticação removidos com sucesso!")
        )
