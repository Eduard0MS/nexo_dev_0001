#!/usr/bin/env python3
"""
Script para reorganizar a estrutura de pastas do projeto Nexo
"""
import os
import shutil
import sys


def reorganizar_estrutura():
    """Reorganiza a estrutura de pastas do projeto"""
    
    # Diretório base
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🔄 Iniciando reorganização da estrutura de pastas...")
    
    # 1. Criar nova estrutura limpa
    nova_estrutura = {
        'projeto': os.path.join(base_dir, 'projeto'),
        'apps': os.path.join(base_dir, 'projeto', 'apps'),
        'config': os.path.join(base_dir, 'projeto', 'config'),
        'static': os.path.join(base_dir, 'projeto', 'static'),
        'media': os.path.join(base_dir, 'projeto', 'media'),
        'templates': os.path.join(base_dir, 'projeto', 'templates'),
        'docs': os.path.join(base_dir, 'docs'),
        'scripts': os.path.join(base_dir, 'scripts'),
        'utils': os.path.join(base_dir, 'utils'),
        'logs': os.path.join(base_dir, 'logs'),
        'backup': os.path.join(base_dir, 'backup')
    }
    
    # Criar diretórios da nova estrutura
    for nome, caminho in nova_estrutura.items():
        os.makedirs(caminho, exist_ok=True)
        print(f"✅ Criado: {nome} -> {caminho}")
    
    # 2. Mapear arquivos e pastas a serem movidos
    mapeamento = {
        # Arquivos principais do Django
        'nexo_dev/nexo/manage.py': 'projeto/manage.py',
        'nexo_dev/nexo/requirements.txt': 'requirements.txt',
        'nexo_dev/nexo/.gitignore': '.gitignore',
        
        # Configurações do Django (Nexus -> config)
        'nexo_dev/nexo/Nexus/': 'projeto/config/',
        
        # Aplicação core
        'nexo_dev/nexo/core/': 'projeto/apps/core/',
        
        # Arquivos estáticos e templates
        'nexo_dev/nexo/static/': 'projeto/static/',
        'nexo_dev/nexo/media/': 'projeto/media/',
        'nexo_dev/nexo/templates/': 'projeto/templates/',
        
        # Documentação
        'nexo_dev/nexo/docs/': 'docs/',
        'nexo_dev/nexo/README.md': 'docs/README.md',
        'nexo_dev/nexo/DOCUMENTACAO_CORRIGIDA.md': 'docs/DOCUMENTACAO_CORRIGIDA.md',
        'nexo_dev/nexo/SISTEMA_RELATORIOS.md': 'docs/SISTEMA_RELATORIOS.md',
        'nexo_dev/nexo/RESUMO_IMPLEMENTACAO.md': 'docs/RESUMO_IMPLEMENTACAO.md',
        'nexo_dev/nexo/PRODUCAO.md': 'docs/PRODUCAO.md',
        'nexo_dev/nexo/PROTECAO-RANSOMWARE.md': 'docs/PROTECAO-RANSOMWARE.md',
        
        # Scripts
        'nexo_dev/nexo/scripts/': 'scripts/',
        'nexo_dev/nexo/utils/': 'utils/',
        
        # Logs
        'nexo_dev/nexo/logs/': 'logs/',
        
        # Backup
        'nexo_dev_backup/': 'backup/old_structure/',
        
        # Banco de dados (manter na raiz do projeto)
        'nexo_dev/nexo/db.sqlite3': 'projeto/db.sqlite3',
        'nexo_dev/nexo/db.sqlite3.backup': 'backup/db.sqlite3.backup',
        
        # Arquivos de configuração Python
        'nexo_dev/nexo/gunicorn_config.py': 'projeto/gunicorn_config.py',
        
        # Scripts Python específicos
        'nexo_dev/nexo/criar_dados_exemplo.py': 'scripts/criar_dados_exemplo.py',
        'nexo_dev/nexo/setup_microsoft_app.py': 'scripts/setup_microsoft_app.py',
        'nexo_dev/nexo/setup_social_app.py': 'scripts/setup_social_app.py',
        'nexo_dev/nexo/patch_adapter.py': 'scripts/patch_adapter.py',
        'nexo_dev/nexo/patch_allauth.py': 'scripts/patch_allauth.py',
        'nexo_dev/nexo/reset_db.py': 'scripts/reset_db.py',
        'nexo_dev/nexo/fix_indentation.py': 'scripts/fix_indentation.py',
        'nexo_dev/nexo/fix_social_app.py': 'scripts/fix_social_app.py',
        'nexo_dev/nexo/inspect_db.py': 'scripts/inspect_db.py',
        'nexo_dev/nexo/check_mysql.py': 'scripts/check_mysql.py',
        'nexo_dev/nexo/check_production.py': 'scripts/check_production.py',
        'nexo_dev/nexo/clean_db.py': 'scripts/clean_db.py',
        'nexo_dev/nexo/create_tables.py': 'scripts/create_tables.py',
        'nexo_dev/nexo/test_table.py': 'scripts/test_table.py',
        
        # Arquivos de resultado/saída
        'resultado_pontos_cargos.json': 'logs/resultado_pontos_cargos.json',
        'resultado_teste.txt': 'logs/resultado_teste.txt',
        'output.txt': 'logs/output.txt',
    }
    
    # 3. Mover arquivos e pastas
    for origem, destino in mapeamento.items():
        origem_path = os.path.join(base_dir, origem)
        destino_path = os.path.join(base_dir, destino)
        
        if os.path.exists(origem_path):
            try:
                # Criar diretório pai se não existir
                os.makedirs(os.path.dirname(destino_path), exist_ok=True)
                
                if os.path.isdir(origem_path):
                    if os.path.exists(destino_path):
                        shutil.rmtree(destino_path)
                    shutil.copytree(origem_path, destino_path)
                    print(f"📁 Movido: {origem} -> {destino}")
                else:
                    shutil.copy2(origem_path, destino_path)
                    print(f"📄 Movido: {origem} -> {destino}")
                    
            except Exception as e:
                print(f"❌ Erro ao mover {origem}: {e}")
        else:
            print(f"⚠️ Não encontrado: {origem}")
    
    print("\n🔧 Atualizando configurações...")
    
    # 4. Atualizar settings.py para nova estrutura
    atualizar_settings()
    
    # 5. Criar __init__.py nos diretórios necessários
    criar_init_files()
    
    print("\n✅ Reorganização concluída!")
    print("\n📁 Nova estrutura:")
    print("├── projeto/")
    print("│   ├── config/          # Configurações Django (antigo Nexus)")
    print("│   ├── apps/")
    print("│   │   └── core/        # Aplicação principal")
    print("│   ├── static/          # Arquivos estáticos")
    print("│   ├── media/           # Uploads")
    print("│   ├── templates/       # Templates")
    print("│   ├── manage.py")
    print("│   └── db.sqlite3")
    print("├── docs/                # Documentação")
    print("├── scripts/             # Scripts auxiliares")
    print("├── utils/               # Utilitários")
    print("├── logs/                # Logs e resultados")
    print("├── backup/              # Backups")
    print("└── requirements.txt")


def atualizar_settings():
    """Atualiza o settings.py para refletir a nova estrutura"""
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projeto', 'config', 'settings.py')
    
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Atualizar referências para a nova estrutura
        conteudo = conteudo.replace("'core'", "'apps.core'")
        conteudo = conteudo.replace("ROOT_URLCONF = 'Nexus.urls'", "ROOT_URLCONF = 'config.urls'")
        conteudo = conteudo.replace("WSGI_APPLICATION = 'Nexus.wsgi.application'", "WSGI_APPLICATION = 'config.wsgi.application'")
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print("⚙️ Settings.py atualizado")


def criar_init_files():
    """Cria arquivos __init__.py necessários"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    init_dirs = [
        'projeto/apps',
        'projeto/apps/core',
        'utils',
        'scripts'
    ]
    
    for dir_path in init_dirs:
        init_file = os.path.join(base_dir, dir_path, '__init__.py')
        if not os.path.exists(init_file):
            os.makedirs(os.path.dirname(init_file), exist_ok=True)
            with open(init_file, 'w') as f:
                f.write('# -*- coding: utf-8 -*-\n')
            print(f"📝 Criado: {init_file}")


if __name__ == '__main__':
    try:
        reorganizar_estrutura()
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante a reorganização: {e}")
        sys.exit(1) 