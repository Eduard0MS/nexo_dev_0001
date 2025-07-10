#!/usr/bin/env python3
import subprocess
import time
import sys
from datetime import datetime

def verificar_status_git():
    """Verifica se há commits pendentes"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) == 0
    except:
        return False

def verificar_gunicorn():
    """Verifica status do gunicorn"""
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'gunicorn_nexo'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def verificar_aplicacao():
    """Verifica se aplicação responde"""
    try:
        result = subprocess.run(['curl', '-f', 'http://localhost:8000'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def main():
    print("🔍 MONITOR DE DEPLOY - NEXO")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    while True:
        print(f"\n📊 Status em {datetime.now().strftime('%H:%M:%S')}:")
        
        # Git Status
        git_ok = verificar_status_git()
        print(f"📦 Git Sync: {'✅ Limpo' if git_ok else '⏳ Pendente'}")
        
        # Gunicorn Status  
        gunicorn_ok = verificar_gunicorn()
        print(f"🔧 Gunicorn: {'✅ Ativo' if gunicorn_ok else '❌ Inativo'}")
        
        # Aplicação Status
        app_ok = verificar_aplicacao()
        print(f"🌐 Aplicação: {'✅ Respondendo' if app_ok else '⏳ Carregando'}")
        
        if git_ok and gunicorn_ok and app_ok:
            print("\n🎉 DEPLOY COMPLETO E FUNCIONAL!")
            break
            
        print("⏳ Aguardando deploy... (Ctrl+C para sair)")
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor interrompido pelo usuário")
        sys.exit(0) 