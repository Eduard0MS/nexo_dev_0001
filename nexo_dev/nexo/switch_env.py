#!/usr/bin/env python3
"""
Script para alternar entre ambientes de desenvolvimento e produção
"""

import os
import sys
from pathlib import Path

def switch_environment(env_type):
    """Altera a variável DJANGO_ENVIRONMENT no arquivo .env"""
    
    # Caminho para o arquivo .env
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return False
    
    # Ler o arquivo atual
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Procurar e alterar a linha DJANGO_ENVIRONMENT
    found = False
    for i, line in enumerate(lines):
        if line.startswith('DJANGO_ENVIRONMENT='):
            lines[i] = f'DJANGO_ENVIRONMENT={env_type}\n'
            found = True
            break
    
    if not found:
        print("❌ Variável DJANGO_ENVIRONMENT não encontrada no arquivo .env!")
        return False
    
    # Escrever o arquivo atualizado
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Ambiente alterado para: {env_type}")
    return True

def show_current_environment():
    """Mostra o ambiente atual"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('DJANGO_ENVIRONMENT='):
                current_env = line.strip().split('=')[1]
                print(f"🌍 Ambiente atual: {current_env}")
                return
    
    print("❌ Variável DJANGO_ENVIRONMENT não encontrada!")

def main():
    if len(sys.argv) < 2:
        print("🔧 Script para alternar entre ambientes")
        print("\nUso:")
        print("  python switch_env.py dev     - Configura para desenvolvimento")
        print("  python switch_env.py prod    - Configura para produção")
        print("  python switch_env.py status  - Mostra ambiente atual")
        print("\nExemplos:")
        print("  python switch_env.py dev")
        print("  python switch_env.py prod")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'dev':
        switch_environment('development')
    elif command == 'prod':
        switch_environment('production')
    elif command == 'status':
        show_current_environment()
    else:
        print(f"❌ Comando inválido: {command}")
        print("Comandos válidos: dev, prod, status")

if __name__ == "__main__":
    main() 