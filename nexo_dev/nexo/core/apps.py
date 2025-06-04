from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Garante que o SocialApp do Google existe e contém as credenciais corretas
        provenientes das variáveis de ambiente. Isso evita erros de client_id ausente
        quando o registro no banco de dados estiver inconsistente ou ainda não criado.
        """
        import os
        from django.conf import settings
        from django.db import connections
        from django.db.utils import OperationalError, ProgrammingError

        # 1) Verifica se o banco está disponível e se a tabela django_site existe
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'django_site'")
                if not cursor.fetchone():
                    return
        except (OperationalError, ProgrammingError):
            # banco ainda não migrado ou indisponível → sai sem levantar
            return

        # 2) Tenta importar os modelos de allauth
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
        except ImportError:
            return

        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        secret    = os.environ.get('GOOGLE_CLIENT_SECRET')
        if not client_id or not secret:
            return

        # 3) Garante que o Site existe
        site_obj, _ = Site.objects.get_or_create(
            id=getattr(settings, 'SITE_ID', 1),
            defaults={
                'domain': '127.0.0.1:8000' if settings.DEBUG else 'example.com',
                'name':   'Nexo Local Development' if settings.DEBUG else 'Nexo',
            }
        )

        # 4) Cria/atualiza o SocialApp do Google
        apps_qs = SocialApp.objects.filter(provider='google')
        if not apps_qs.exists():
            app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth',
                client_id=client_id,
                secret=secret,
                key='',
            )
            app.sites.add(site_obj)
            return

        # Mantenha apenas um registro “principal”
        primary = apps_qs.first()
        for other in apps_qs.exclude(id=primary.id):
            if not other.client_id:
                other.delete()
            else:
                primary = other

        # Atualiza credenciais caso necessário
        updated = False
        if primary.client_id != client_id:
            primary.client_id = client_id
            updated = True
        if primary.secret != secret:
            primary.secret = secret
            updated = True
        if updated:
            primary.name = 'Google OAuth'
            primary.save()

        if site_obj not in primary.sites.all():
            primary.sites.add(site_obj)
