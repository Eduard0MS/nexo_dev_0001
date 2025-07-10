from django.apps import AppConfig
from django.contrib import admin


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        """Garante que o SocialApp do Google existe e contém as credenciais corretas
        provenientes das variáveis de ambiente. Isso evita erros de client_id ausente
        quando o registro no banco de dados estiver inconsistente ou ainda não criado.
        """
        # Executar apenas se o allauth estiver instalado
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
            import os
            from django.conf import settings
        except Exception:
            return  # Se dependências não estiverem disponíveis (por exemplo, migrações), saia

        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        secret = os.environ.get('GOOGLE_CLIENT_SECRET')

        # Se não houver credenciais, não há nada a sincronizar
        if not client_id or not secret:
            return

        # Garante que o site padrão exista
        site, _ = Site.objects.get_or_create(
            id=getattr(settings, 'SITE_ID', 1),
            defaults={
                'domain': '127.0.0.1:8000' if settings.DEBUG else 'example.com',
                'name': 'Nexo Local Development' if settings.DEBUG else 'Nexo',
            },
        )

        # Cria ou atualiza o SocialApp
        apps_qs = SocialApp.objects.filter(provider='google')

        # Se não existir nenhum cria um novo
        if not apps_qs.exists():
            app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth',
                client_id=client_id,
                secret=secret,
                key='',
            )
            app.sites.add(site)
            return

        # Caso exista mais de um, mantenha o primeiro e sincronize-o; elimine duplicatas vazias
        primary = apps_qs.first()
        for duplicate in apps_qs.exclude(id=primary.id):
            if duplicate.client_id == '' or duplicate.client_id is None:
                duplicate.delete()
            else:
                primary = duplicate  # prefere registro com dados reais

        # Atualiza o registro primário com as variáveis de ambiente se necessário
        changed = False
        if primary.client_id != client_id:
            primary.client_id = client_id
            changed = True
        if primary.secret != secret:
            primary.secret = secret
            changed = True
        if changed:
            primary.name = 'Google OAuth'
            primary.save()

        # Garante associação ao site
        if site not in primary.sites.all():
            primary.sites.add(site)

        # Customizar o admin quando o app iniciar
        admin.site.site_header = "Administração do Nexo"
        admin.site.site_title = "Nexo"
        admin.site.index_title = "Administração do Sistema"
