#!/usr/bin/env python
"""
Script para configurar aplicações sociais OAuth (Google, Microsoft)
Automatiza a configuração do Django AllAuth
"""

import os
import sys
import django
from dotenv import load_dotenv

# Adicionar o diretório raiz do projeto ao Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def setup_google_oauth():
    """Configurar Google OAuth"""
    print("🔧 Configurando Google OAuth...")
    
    # Obter credenciais do ambiente
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERRO: GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET devem estar definidos no .env")
        return False
        
    if client_id == "YOUR_CLIENT_ID_HERE" or client_secret == "YOUR_CLIENT_SECRET_HERE":
        print("❌ ERRO: Configure valores reais para GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET")
        return False
    
    try:
        # Configurar o aplicativo Google
        google_app, created = SocialApp.objects.get_or_create(
            provider="google",
            defaults={
                "name": "Google OAuth",
                "client_id": client_id,
                "secret": client_secret,
                "key": "",
            },
        )
        
        if not created:
            # Atualizar credenciais se o app já existe
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            print("🔄 Aplicativo Google OAuth atualizado")
        else:
            print("✅ Aplicativo Google OAuth criado")
        
        # Verificar e configurar site
        site = setup_site()
        if site:
            google_app.sites.add(site)
            print(f"🔗 Aplicativo associado ao site: {site.domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Google OAuth: {str(e)}")
        return False

def setup_microsoft_oauth():
    """Configurar Microsoft OAuth"""
    print("🔧 Configurando Microsoft OAuth...")
    
    # Obter credenciais do ambiente
    client_id = os.environ.get("MICROSOFT_CLIENT_ID")
    client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("⚠️  AVISO: MICROSOFT_CLIENT_ID e MICROSOFT_CLIENT_SECRET não definidos")
        print("   Pulando configuração do Microsoft OAuth")
        return True
    
    try:
        # Configurar o aplicativo Microsoft
        microsoft_app, created = SocialApp.objects.get_or_create(
            provider="microsoft",
            defaults={
                "name": "Microsoft OAuth",
                "client_id": client_id,
                "secret": client_secret,
                "key": "",
            },
        )
        
        if not created:
            # Atualizar credenciais se o app já existe
            microsoft_app.client_id = client_id
            microsoft_app.secret = client_secret
            microsoft_app.save()
            print("🔄 Aplicativo Microsoft OAuth atualizado")
        else:
            print("✅ Aplicativo Microsoft OAuth criado")
        
        # Verificar e configurar site
        site = setup_site()
        if site:
            microsoft_app.sites.add(site)
            print(f"🔗 Aplicativo associado ao site: {site.domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Microsoft OAuth: {str(e)}")
        return False

def setup_site():
    """Configurar site padrão"""
    environment = os.environ.get("DJANGO_ENVIRONMENT", "development")
    
    if environment == "production":
        # Em produção, usar domínio real
        domain = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")[0]
        if not domain or domain == "*":
            print("⚠️  AVISO: Configure DJANGO_ALLOWED_HOSTS para produção")
            domain = "example.com"
        name = "Nexo Production"
    else:
        # Em desenvolvimento, usar localhost
        domain = "localhost:8000"
        name = "Nexo Development"
    
    try:
        site, created = Site.objects.get_or_create(
            id=1, 
            defaults={"domain": domain, "name": name}
        )
        
        if not created:
            # Atualizar site existente
            site.domain = domain
            site.name = name
            site.save()
            print(f"🔄 Site atualizado: {site.domain}")
        else:
            print(f"✅ Site criado: {site.domain}")
            
        return site
        
    except Exception as e:
        print(f"❌ Erro ao configurar site: {str(e)}")
        return None

def verify_oauth_setup():
    """Verificar se o OAuth está configurado corretamente"""
    print("\n🔍 Verificando configuração OAuth...")
    
    try:
        # Verificar Google
        google_apps = SocialApp.objects.filter(provider="google")
        if google_apps.exists():
            print("✅ Google OAuth configurado")
            for app in google_apps:
                print(f"   Nome: {app.name}")
                print(f"   Client ID: {app.client_id[:10]}...")
                print(f"   Sites: {[s.domain for s in app.sites.all()]}")
        else:
            print("❌ Google OAuth não configurado")
        
        # Verificar Microsoft
        microsoft_apps = SocialApp.objects.filter(provider="microsoft")
        if microsoft_apps.exists():
            print("✅ Microsoft OAuth configurado")
            for app in microsoft_apps:
                print(f"   Nome: {app.name}")
                print(f"   Client ID: {app.client_id[:10]}...")
                print(f"   Sites: {[s.domain for s in app.sites.all()]}")
        else:
            print("⚠️  Microsoft OAuth não configurado")
        
        # Verificar site
        try:
            site = Site.objects.get(id=1)
            print(f"✅ Site principal: {site.domain} ({site.name})")
        except Site.DoesNotExist:
            print("❌ Site principal não encontrado")
        
    except Exception as e:
        print(f"❌ Erro na verificação: {str(e)}")

def main():
    """Função principal"""
    print("🚀 Configurador de OAuth - Nexo")
    print("=" * 40)
    
    environment = os.environ.get("DJANGO_ENVIRONMENT", "development")
    print(f"🔧 Ambiente: {environment}")
    
    success = True
    
    # Configurar Google OAuth
    if not setup_google_oauth():
        success = False
    
    # Configurar Microsoft OAuth (opcional)
    if not setup_microsoft_oauth():
        success = False
    
    # Verificar configuração
    verify_oauth_setup()
    
    if success:
        print("\n✅ Configuração OAuth concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("1. Verifique as URLs de callback nos consoles OAuth:")
        print("   - Google: https://console.developers.google.com/")
        print("   - Microsoft: https://portal.azure.com/")
        print("2. URLs de callback para configurar:")
        if environment == "production":
            domain = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")[0]
            print(f"   - Google: https://{domain}/accounts/google/login/callback/")
            print(f"   - Microsoft: https://{domain}/accounts/microsoft/login/callback/")
        else:
            print("   - Google: http://localhost:8000/accounts/google/login/callback/")
            print("   - Microsoft: http://localhost:8000/accounts/microsoft/login/callback/")
    else:
        print("\n❌ Houve problemas na configuração OAuth")
        print("Verifique os erros acima e corrija antes de continuar")
        sys.exit(1)

if __name__ == "__main__":
    main()