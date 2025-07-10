#!/usr/bin/env python
"""
Script para verificar se o sistema CI/CD está pronto para uso.
Executa uma série de verificações e mostra o status atual.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_check(description, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {description}")
    if details:
        print(f"   └─ {details}")

def check_file_exists(filepath, description):
    exists = Path(filepath).exists()
    print_check(description, exists, filepath if exists else f"Arquivo não encontrado: {filepath}")
    return exists

def check_github_workflow():
    print_header("VERIFICAÇÃO DO WORKFLOW GITHUB ACTIONS")
    
    workflow_file = ".github/workflows/ci-cd.yml"
    exists = check_file_exists(workflow_file, "Arquivo de workflow existe")
    
    if exists:
        with open(workflow_file, 'r') as f:
            content = f.read()
            
        # Verificar jobs essenciais
        jobs = ['test:', 'security:', 'build-and-deploy:', 'notify:']
        all_jobs_present = all(job in content for job in jobs)
        print_check("Todos os jobs estão presentes", all_jobs_present, 
                   f"Jobs: {', '.join(jobs)}")
        
        # Verificar secrets
        secrets_used = content.count('secrets.')
        print_check("Secrets configurados no workflow", secrets_used > 0, 
                   f"{secrets_used} referências a secrets encontradas")
        
        return all_jobs_present
    
    return False

def check_dependencies():
    print_header("VERIFICAÇÃO DE DEPENDÊNCIAS")
    
    requirements_file = "nexo_dev/nexo/requirements.txt"
    exists = check_file_exists(requirements_file, "Arquivo requirements.txt existe")
    
    if exists:
        with open(requirements_file, 'r') as f:
            content = f.read()
            
        # Verificar dependências essenciais para CI/CD
        essential_deps = ['Django', 'flake8', 'black', 'pytest', 'coverage']
        deps_found = []
        
        for dep in essential_deps:
            if dep.lower() in content.lower():
                deps_found.append(dep)
        
        all_deps_present = len(deps_found) >= 3  # Pelo menos 3 dependências essenciais
        print_check("Dependências essenciais presentes", all_deps_present,
                   f"Encontradas: {', '.join(deps_found)}")
        
        return all_deps_present
    
    return False

def check_test_files():
    print_header("VERIFICAÇÃO DE TESTES")
    
    test_files = [
        "nexo_dev/nexo/scripts/run_all_tests.py",
        "nexo_dev/nexo/scripts/test_autenticacao.py", 
        "nexo_dev/nexo/scripts/test_financeiro.py",
        "nexo_dev/nexo/scripts/test_organograma.py",
        "nexo_dev/nexo/core/tests.py"
    ]
    
    tests_found = 0
    for test_file in test_files:
        if check_file_exists(test_file, f"Teste: {os.path.basename(test_file)}"):
            tests_found += 1
    
    adequate_tests = tests_found >= 3
    print_check("Testes adequados implementados", adequate_tests,
               f"{tests_found}/{len(test_files)} arquivos de teste encontrados")
    
    return adequate_tests

def check_production_config():
    print_header("VERIFICAÇÃO DE CONFIGURAÇÃO DE PRODUÇÃO")
    
    config_files = [
        "nexo_dev/nexo/check_production.py",
        "nexo_dev/nexo/gunicorn_config.py", 
        "nexo_dev/nexo/Nexus/wsgi_prod.py",
        "Dockerfile"
    ]
    
    configs_found = 0
    for config_file in config_files:
        if check_file_exists(config_file, f"Config: {os.path.basename(config_file)}"):
            configs_found += 1
    
    adequate_config = configs_found >= 3
    print_check("Configurações de produção adequadas", adequate_config,
               f"{configs_found}/{len(config_files)} arquivos de configuração encontrados")
    
    return adequate_config

def check_docker_setup():
    print_header("VERIFICAÇÃO DE CONTAINERIZAÇÃO")
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    docker_ready = all(check_file_exists(f, f"Docker: {f}") for f in docker_files)
    print_check("Containerização pronta", docker_ready)
    
    return docker_ready

def check_environment_vars():
    print_header("VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE")
    
    # Verificar se arquivo .env existe
    env_file_exists = check_file_exists("nexo_dev/nexo/.env", "Arquivo .env local")
    
    # Verificar variáveis críticas no sistema
    critical_vars = [
        'DJANGO_SECRET_KEY',
        'DATABASE_URL', 
        'ALLOWED_HOSTS',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET'
    ]
    
    vars_set = []
    for var in critical_vars:
        if os.environ.get(var):
            vars_set.append(var)
    
    adequate_vars = len(vars_set) >= 2  # Pelo menos algumas variáveis configuradas
    print_check("Variáveis de ambiente configuradas", adequate_vars,
               f"{len(vars_set)}/{len(critical_vars)} variáveis encontradas")
    
    return env_file_exists or adequate_vars

def generate_summary(checks_results):
    print_header("RESUMO FINAL")
    
    total_checks = len(checks_results)
    passed_checks = sum(checks_results.values())
    percentage = (passed_checks / total_checks) * 100
    
    print(f"📊 Total de verificações: {total_checks}")
    print(f"✅ Verificações passaram: {passed_checks}")
    print(f"❌ Verificações falharam: {total_checks - passed_checks}")
    print(f"📈 Percentual de prontidão: {percentage:.1f}%")
    
    if percentage >= 80:
        print(f"\n🎉 PARABÉNS! Seu sistema CI/CD está {percentage:.1f}% pronto!")
        print("📋 Siga o arquivo SETUP_CICD.md para completar os itens restantes.")
        status = "PRONTO"
    elif percentage >= 60:
        print(f"\n⚠️  Seu sistema CI/CD está {percentage:.1f}% pronto.")
        print("🔧 Alguns ajustes são necessários. Consulte SETUP_CICD.md")
        status = "QUASE PRONTO"
    else:
        print(f"\n🚨 Seu sistema CI/CD precisa de mais configuração ({percentage:.1f}% pronto).")
        print("📚 Siga o guia completo em SETUP_CICD.md")
        status = "PRECISA CONFIGURAÇÃO"
    
    return status, percentage

def main():
    print("🔍 VERIFICADOR DE PRONTIDÃO CI/CD - PROJETO NEXO")
    print("Este script verifica se seu sistema CI/CD está pronto para uso.\n")
    
    # Mudar para o diretório do projeto se necessário
    if os.path.exists("nexo_dev_0001"):
        os.chdir("nexo_dev_0001")
        print("📁 Navegando para o diretório do projeto...")
    
    # Executar verificações
    checks = {
        "GitHub Workflow": check_github_workflow(),
        "Dependências": check_dependencies(), 
        "Testes": check_test_files(),
        "Configuração de Produção": check_production_config(),
        "Docker": check_docker_setup(),
        "Variáveis de Ambiente": check_environment_vars()
    }
    
    # Gerar resumo
    status, percentage = generate_summary(checks)
    
    # Salvar relatório
    report = {
        "timestamp": str(subprocess.check_output(['date'], text=True).strip()),
        "status": status,
        "percentage": percentage,
        "checks": checks
    }
    
    with open("cicd_check_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Relatório salvo em: cicd_check_report.json")
    print("\n📖 Para próximos passos, consulte: SETUP_CICD.md")
    
    return 0 if percentage >= 80 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 