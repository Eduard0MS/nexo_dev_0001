#!/usr/bin/env python
"""
Script para testar a proteção contra ransomware do Nexo.
Este script simula comportamentos de ransomware para verificar se o sistema
de proteção está funcionando corretamente.
"""

import os
import sys
import time
import random
import string
import logging
import shutil
from pathlib import Path
import argparse

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ransomware_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ransomware_test")

# Obter o diretório base
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretórios de teste
TEST_DIR = os.path.join(BASE_DIR, "test_files")


def setup_test_environment():
    """Prepara o ambiente de teste."""
    logger.info("Configurando ambiente de teste")

    # Criar diretório de teste, se não existir
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
        logger.info(f"Diretório de teste criado: {TEST_DIR}")

    # Criar arquivos de teste
    for i in range(10):
        file_path = os.path.join(TEST_DIR, f"test_file_{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"Este é um arquivo de teste {i}\n")
            f.write("Conteúdo para teste de proteção contra ransomware.\n")
            f.write("".join(random.choice(string.ascii_letters) for _ in range(100)))

        logger.info(f"Arquivo de teste criado: {file_path}")

    logger.info("Ambiente de teste configurado com sucesso")


def test_mass_changes(num_files=30, pause=0.1):
    """
    Testa a detecção de alterações em massa modificando vários arquivos rapidamente.
    Isso deve acionar o alerta de possível ransomware.
    """
    logger.info(f"Iniciando teste de alterações em massa em {num_files} arquivos")

    # Criar arquivos adicionais para o teste
    for i in range(num_files):
        file_path = os.path.join(TEST_DIR, f"mass_change_test_{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"Arquivo para teste de alterações em massa {i}\n")
            f.write("".join(random.choice(string.ascii_letters) for _ in range(50)))

    # Modificar todos os arquivos rapidamente
    logger.info("Modificando arquivos rapidamente...")

    for i in range(num_files):
        file_path = os.path.join(TEST_DIR, f"mass_change_test_{i}.txt")
        time.sleep(pause)  # Pequena pausa para simular operações reais

        with open(file_path, "a") as f:
            f.write(f"\nArquivo modificado em massa no teste {i}\n")
            f.write("".join(random.choice(string.ascii_letters) for _ in range(50)))

    logger.info(f"Teste concluído: {num_files} arquivos modificados rapidamente")
    logger.info("Verifique logs/ransomware_monitor.log para ver se o alerta foi gerado")


def test_extension_changes():
    """
    Testa a detecção de alterações de extensão de arquivo.
    Modifica extensões para aquelas tipicamente usadas por ransomware.
    """
    logger.info("Iniciando teste de alterações de extensão")

    # Criar arquivos para teste
    extensions = ["txt", "doc", "pdf", "jpg", "png"]
    ransomware_extensions = [".encrypted", ".locked", ".crypto", ".crypt", ".wncry"]

    test_files = []

    # Criar arquivos com extensões normais
    for ext in extensions:
        file_path = os.path.join(TEST_DIR, f"ext_test.{ext}")
        with open(file_path, "w") as f:
            f.write(f"Arquivo para teste de alteração de extensão .{ext}\n")
            f.write("".join(random.choice(string.ascii_letters) for _ in range(50)))
        test_files.append(file_path)

    logger.info(f"Criados {len(test_files)} arquivos para teste de extensão")

    # Modificar extensões para simulação de ransomware
    for i, file_path in enumerate(test_files):
        if i >= len(ransomware_extensions):
            break

        new_path = f"{file_path}{ransomware_extensions[i]}"
        os.rename(file_path, new_path)
        logger.info(f"Renomeado: {file_path} -> {new_path}")

    logger.info("Teste de alteração de extensão concluído")
    logger.info("Verifique logs/ransomware_monitor.log para ver se o alerta foi gerado")


def test_ransom_note():
    """
    Testa a detecção de notas de resgate típicas de ransomware.
    Cria arquivos com nomes e conteúdos comuns encontrados nesses ataques.
    """
    logger.info("Iniciando teste de criação de notas de resgate")

    ransom_note_names = [
        "README_TO_DECRYPT.txt",
        "HOW_TO_DECRYPT_FILES.txt",
        "YOUR_FILES_ARE_ENCRYPTED.txt",
        "DECRYPT_INSTRUCTION.txt",
        "RECOVERY_KEY.txt",
    ]

    for name in ransom_note_names:
        file_path = os.path.join(TEST_DIR, name)
        with open(file_path, "w") as f:
            f.write("SEUS ARQUIVOS FORAM CRIPTOGRAFADOS!\n\n")
            f.write(
                "Para recuperar seus arquivos, você precisa pagar um resgate de 1 Bitcoin.\n"
            )
            f.write(
                "Entre em contato com hack3r@malici0us-domain.com para instruções de pagamento.\n"
            )
            f.write(
                "\nVocê tem 72 horas para pagar, ou seus arquivos serão deletados permanentemente.\n"
            )

        logger.info(f"Nota de resgate criada: {file_path}")

    logger.info("Teste de criação de notas de resgate concluído")
    logger.info(
        "Verifique logs/ransomware_monitor.log para ver se as notas foram detectadas"
    )


def cleanup():
    """Limpa o ambiente de teste removendo os arquivos criados."""
    logger.info("Iniciando limpeza do ambiente de teste")

    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
        logger.info(f"Diretório de teste removido: {TEST_DIR}")

    logger.info("Limpeza concluída")


def main():
    parser = argparse.ArgumentParser(description="Teste de proteção contra ransomware")
    parser.add_argument("--all", action="store_true", help="Executa todos os testes")
    parser.add_argument(
        "--mass-changes",
        action="store_true",
        help="Testa detecção de alterações em massa",
    )
    parser.add_argument(
        "--extension",
        action="store_true",
        help="Testa detecção de alterações de extensão",
    )
    parser.add_argument(
        "--ransom-note", action="store_true", help="Testa detecção de notas de resgate"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Não remove os arquivos de teste após a execução",
    )
    args = parser.parse_args()

    # Se nenhum teste específico for solicitado, executa todos
    run_all = args.all or not (args.mass_changes or args.extension or args.ransom_note)

    try:
        logger.info("Iniciando testes de proteção contra ransomware")
        setup_test_environment()

        if run_all or args.mass_changes:
            test_mass_changes()
            time.sleep(5)  # Dar tempo para o monitor detectar

        if run_all or args.extension:
            test_extension_changes()
            time.sleep(5)  # Dar tempo para o monitor detectar

        if run_all or args.ransom_note:
            test_ransom_note()
            time.sleep(5)  # Dar tempo para o monitor detectar

        logger.info("Todos os testes concluídos")

        if not args.no_cleanup:
            cleanup()

    except Exception as e:
        logger.error(f"Erro durante os testes: {str(e)}")
        if not args.no_cleanup:
            cleanup()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
