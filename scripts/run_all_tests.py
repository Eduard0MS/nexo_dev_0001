#!/usr/bin/env python
"""
Script para executar todos os testes do sistema Nexo.
Este script executa todos os testes criados para cada componente do sistema.
"""

import os
import sys
import logging
import subprocess
import datetime
import time
from pathlib import Path
import argparse

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/all_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('all_tests')

# Diretório base
BASE_DIR = Path(__file__).resolve().parent.parent

# Lista de scripts de teste a serem executados
TEST_SCRIPTS = [
    'scripts/test_ransomware_protection.py',
    'scripts/test_backup_system.py',
    'scripts/test_organograma.py',
    'scripts/test_financeiro.py',
    'scripts/test_autenticacao.py',
    'scripts/test_sql_injection.py'
]

def ensure_directories():
    """Garante que os diretórios necessários existem."""
    os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'backups'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'backups', 'snapshots'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'backups', 'quarantine'), exist_ok=True)
    
    logger.info("Diretórios de teste garantidos")

def run_test(script_path):
    """Executa um script de teste e retorna o resultado."""
    start_time = time.time()
    full_path = os.path.join(BASE_DIR, script_path)
    
    logger.info(f"Executando teste: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, full_path],
            capture_output=True,
            text=True
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            logger.info(f"Teste concluído com sucesso: {script_path} (tempo: {execution_time:.2f}s)")
            return True, result.stdout, execution_time
        else:
            logger.error(f"Teste falhou: {script_path} (tempo: {execution_time:.2f}s)")
            logger.error(f"Saída de erro: {result.stderr}")
            return False, result.stderr, execution_time
            
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        logger.error(f"Erro ao executar teste {script_path}: {str(e)} (tempo: {execution_time:.2f}s)")
        return False, str(e), execution_time

def run_all_tests():
    """Executa todos os testes e gera um relatório."""
    results = []
    total_start_time = time.time()
    
    ensure_directories()
    
    for script in TEST_SCRIPTS:
        success, output, execution_time = run_test(script)
        results.append({
            'script': script,
            'success': success,
            'output': output,
            'execution_time': execution_time
        })
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # Gerar relatório
    successful_tests = sum(1 for result in results if result['success'])
    failed_tests = len(results) - successful_tests
    
    report = "\n" + "=" * 80 + "\n"
    report += f"RELATÓRIO DE TESTES - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += "=" * 80 + "\n\n"
    
    report += f"Total de testes executados: {len(results)}\n"
    report += f"Testes bem-sucedidos: {successful_tests}\n"
    report += f"Testes falhos: {failed_tests}\n"
    report += f"Tempo total de execução: {total_execution_time:.2f} segundos\n\n"
    
    report += "Detalhes dos testes:\n"
    report += "-" * 80 + "\n"
    
    for result in results:
        status = "SUCESSO" if result['success'] else "FALHA"
        report += f"{result['script']} - {status} - {result['execution_time']:.2f}s\n"
    
    report += "\n" + "=" * 80 + "\n"
    
    # Salvar relatório em arquivo
    report_path = os.path.join(BASE_DIR, 'logs', f"test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Relatório de testes salvo em: {report_path}")
    
    # Exibir relatório
    print(report)
    
    # Retornar código de saída apropriado
    return 0 if failed_tests == 0 else 1

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Executa todos os testes do sistema Nexo')
    parser.add_argument('--skip', type=str, help='Lista de scripts a serem ignorados, separados por vírgula')
    args = parser.parse_args()
    
    # Filtrar scripts a serem ignorados
    global TEST_SCRIPTS
    if args.skip:
        scripts_to_skip = args.skip.split(',')
        TEST_SCRIPTS = [script for script in TEST_SCRIPTS if script not in scripts_to_skip]
    
    return run_all_tests()

if __name__ == "__main__":
    sys.exit(main()) 