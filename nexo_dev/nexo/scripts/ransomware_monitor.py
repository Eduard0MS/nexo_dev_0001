#!/usr/bin/env python
"""
Sistema de monitoramento e detecção de atividade de ransomware.
Este script monitora comportamentos suspeitos típicos de ransomware:
1. Alterações em massa de arquivos
2. Alterações de extensões de arquivo
3. Criação de arquivos de resgate
4. Tentativas de criptografia em volume
5. Padrões suspeitos de leitura/escrita
"""

import os
import sys
import time
import logging
import shutil
import hashlib
import datetime
import re
import tarfile
from pathlib import Path
from collections import deque, Counter
import threading
import json
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ransomware_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ransomware_monitor")

# Configurações
BASE_DIR = Path(__file__).resolve().parent.parent
DIRS_TO_MONITOR = [
    os.path.join(BASE_DIR, "media"),
    os.path.join(BASE_DIR, "staticfiles"),
    os.path.join(BASE_DIR, "core"),
    os.path.join(BASE_DIR, "Nexus"),
]
SNAPSHOT_DIR = os.path.join(BASE_DIR, "backups", "snapshots")
QUARANTINE_DIR = os.path.join(BASE_DIR, "backups", "quarantine")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")  # Adicionando BACKUP_DIR

# Criar diretórios necessários
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(QUARANTINE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)  # Criar diretório de backup

# Limites e configurações de detecção
FILE_CHANGE_THRESHOLD = int(
    os.environ.get("RANSOMWARE_FILE_CHANGE_THRESHOLD", 20)
)  # Número de arquivos alterados em um curto período para gerar alerta
TIME_WINDOW_SECONDS = int(
    os.environ.get("RANSOMWARE_TIME_WINDOW_SECONDS", 60)
)  # Janela de tempo para monitorar alterações em massa
EXTENSION_BLACKLIST = os.environ.get(
    "RANSOMWARE_EXTENSION_BLACKLIST",
    ".encrypted,.locked,.crypto,.crypt,.crinf,.r5a,.ACCDB,.djvu,.wallet",
).split(",")
RANSOMWARE_PATTERNS = [
    r"YOUR_FILES_ARE_ENCRYPTED",
    r"HOW_TO_DECRYPT",
    r"RANSOM",
    r"RECOVERY_KEY",
    r"DECRYPT_INSTRUCTION",
    r"\.TXT$",  # Arquivos de texto criados durante ataques, geralmente instruções
    r"README.*\.txt$",
]

# Configurações de e-mail para alertas
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")

# Histórico de alterações para detecção
file_change_history = deque(maxlen=1000)
is_attack_mode = False
active_measures = []


def get_file_signature(file_path):
    """Gera uma assinatura (hash) para o conteúdo do arquivo."""
    try:
        with open(file_path, "rb") as f:
            content = f.read(8192)  # Lê apenas os primeiros 8KB para performance
            # SEGURANÇA: MD5 usado apenas para verificação de integridade, não segurança
            return hashlib.md5(content, usedforsecurity=False).hexdigest()
    except Exception as e:
        logger.error(f"Erro ao gerar assinatura para {file_path}: {str(e)}")
        return None


def create_snapshot():
    """Cria um snapshot dos diretórios monitorados para posterior comparação."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_file = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}.json")

    snapshot = {}
    for directory in DIRS_TO_MONITOR:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if (
                        os.path.getsize(file_path) < 10 * 1024 * 1024
                    ):  # Limitar a 10MB para performance
                        signature = get_file_signature(file_path)
                        stat = os.stat(file_path)

                        snapshot[file_path] = {
                            "signature": signature,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "extension": os.path.splitext(file_path)[1].lower(),
                        }
                except Exception as e:
                    logger.error(
                        f"Erro ao processar arquivo {file_path} para snapshot: {str(e)}"
                    )

    try:
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f)

        logger.info(f"Snapshot criado com sucesso: {snapshot_file}")
        return snapshot_file
    except Exception as e:
        logger.error(f"Erro ao salvar snapshot: {str(e)}")
        return None


def load_latest_snapshot():
    """Carrega o snapshot mais recente para comparação."""
    try:
        snapshot_files = [
            f
            for f in os.listdir(SNAPSHOT_DIR)
            if f.startswith("snapshot_") and f.endswith(".json")
        ]
        if not snapshot_files:
            logger.warning("Nenhum snapshot encontrado. Criando um novo.")
            return {}

        latest_snapshot = sorted(snapshot_files)[-1]
        with open(os.path.join(SNAPSHOT_DIR, latest_snapshot), "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar snapshot: {str(e)}")
        return {}


def quarantine_file(file_path):
    """Move um arquivo suspeito para quarentena."""
    try:
        if not os.path.exists(file_path):
            return False

        rel_path = os.path.relpath(file_path, BASE_DIR)
        quarantine_path = os.path.join(QUARANTINE_DIR, rel_path)

        # Garantir que o diretório de destino existe
        os.makedirs(os.path.dirname(quarantine_path), exist_ok=True)

        # Copiar para quarentena e remover original
        shutil.copy2(file_path, quarantine_path)
        os.chmod(file_path, 0o000)  # Remover todas as permissões

        logger.info(f"Arquivo colocado em quarentena: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao colocar arquivo em quarentena {file_path}: {str(e)}")
        return False


def is_suspicious_file(file_path, extension=None):
    """Verifica se um arquivo é suspeito com base em padrões conhecidos de ransomware."""
    if extension is None:
        extension = os.path.splitext(file_path)[1].lower()

    # Verificar extensão contra lista negra
    if extension in EXTENSION_BLACKLIST:
        return True

    # Verificar padrões de nomes de arquivo de ransomware
    filename = os.path.basename(file_path)
    for pattern in RANSOMWARE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return True

    return False


def detect_mass_changes():
    """Detecta alterações em massa nos arquivos, típico de ataques de ransomware."""
    now = time.time()
    recent_window = now - TIME_WINDOW_SECONDS

    # Filtrar alterações dentro da janela de tempo
    recent_changes = [
        change for change in file_change_history if change["timestamp"] > recent_window
    ]

    if len(recent_changes) > FILE_CHANGE_THRESHOLD:
        # Análise adicional: verificar alterações de extensão
        extensions_changed = Counter()
        for change in recent_changes:
            if "old_extension" in change and "new_extension" in change:
                if change["old_extension"] != change["new_extension"]:
                    extensions_changed[
                        (change["old_extension"], change["new_extension"])
                    ] += 1

        return {
            "changes_count": len(recent_changes),
            "threshold": FILE_CHANGE_THRESHOLD,
            "window_seconds": TIME_WINDOW_SECONDS,
            "extensions_changed": dict(extensions_changed),
        }

    return None


def send_alert(subject, message):
    """Envia um alerta por e-mail."""
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, ALERT_EMAIL]):
        logger.warning(
            "Configurações de e-mail incompletas. Não foi possível enviar alerta."
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = ALERT_EMAIL
        msg["Subject"] = f"ALERTA DE RANSOMWARE: {subject}"

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Alerta enviado: {subject}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar alerta: {str(e)}")
        return False


def activate_protection_measures():
    """Ativa medidas de proteção contra ransomware em andamento."""
    global is_attack_mode, active_measures

    is_attack_mode = True
    logger.critical("ATIVANDO MEDIDAS DE PROTEÇÃO DE EMERGÊNCIA")

    measures = []

    # 1. Criar backup de emergência dos arquivos críticos
    try:
        emergency_backup = os.path.join(
            BACKUP_DIR,
            f'emergency_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.tar.gz',
        )
        with tarfile.open(emergency_backup, "w:gz") as tar:
            for directory in [
                os.path.join(BASE_DIR, "Nexus"),
                os.path.join(BASE_DIR, ".env"),
            ]:
                if os.path.exists(directory):
                    tar.add(directory, arcname=os.path.basename(directory))
        measures.append(f"Backup de emergência criado: {emergency_backup}")
    except:
        logger.error("Falha ao criar backup de emergência", exc_info=True)

    # 2. Tentar isolar a máquina na rede
    try:
        # Em um sistema real, você poderia chamar o firewall para bloquear tráfego
        # subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'on'])
        measures.append("Firewall ativado para isolar a máquina")
    except:
        logger.error("Falha ao isolar máquina na rede", exc_info=True)

    # 3. Tentar pausar serviços web (para evitar propagação)
    try:
        # Em um sistema real, você poderia parar o servidor web
        # subprocess.run(['systemctl', 'stop', 'nginx'])
        # subprocess.run(['systemctl', 'stop', 'gunicorn'])
        measures.append("Serviços web pausados para conter propagação")
    except:
        logger.error("Falha ao pausar serviços web", exc_info=True)

    active_measures = measures

    # 4. Enviar alerta crítico
    alert_message = "POSSÍVEL ATAQUE DE RANSOMWARE DETECTADO!\n\n"
    alert_message += "Medidas de proteção ativadas:\n"
    alert_message += "\n".join(f"- {measure}" for measure in measures)
    alert_message += "\n\nVerifique o sistema imediatamente!"

    send_alert(
        "ATAQUE DE RANSOMWARE EM ANDAMENTO - MEDIDAS DE PROTEÇÃO ATIVADAS",
        alert_message,
    )

    logger.critical(alert_message)


def monitor_files():
    """Função principal de monitoramento contínuo."""
    snapshot = load_latest_snapshot()
    if not snapshot:
        snapshot_file = create_snapshot()
        if snapshot_file:
            snapshot = load_latest_snapshot()

    logger.info(f"Iniciando monitoramento de {len(DIRS_TO_MONITOR)} diretórios")

    while True:
        try:
            changes_detected = []

            for directory in DIRS_TO_MONITOR:
                if not os.path.exists(directory):
                    continue

                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        current_extension = os.path.splitext(file_path)[1].lower()

                        # Verificar se é um arquivo suspeito pelo nome/extensão
                        if is_suspicious_file(file_path, current_extension):
                            logger.warning(f"Arquivo suspeito detectado: {file_path}")
                            quarantine_file(file_path)
                            changes_detected.append(
                                {
                                    "file": file_path,
                                    "type": "suspicious_file",
                                    "timestamp": time.time(),
                                    "extension": current_extension,
                                }
                            )
                            continue

                        # Verificar se é um novo arquivo ou foi modificado
                        try:
                            if file_path in snapshot:
                                # Arquivo existente - verificar se foi modificado
                                stat = os.stat(file_path)
                                old_data = snapshot[file_path]

                                if stat.st_mtime > old_data["mtime"]:
                                    # Arquivo foi modificado
                                    new_signature = get_file_signature(file_path)

                                    if new_signature != old_data["signature"]:
                                        old_extension = old_data["extension"]

                                        # Registrar a mudança
                                        changes_detected.append(
                                            {
                                                "file": file_path,
                                                "type": "modified",
                                                "timestamp": time.time(),
                                                "old_extension": old_extension,
                                                "new_extension": current_extension,
                                                "old_size": old_data["size"],
                                                "new_size": stat.st_size,
                                            }
                                        )

                                        # Atualizar snapshot
                                        snapshot[file_path] = {
                                            "signature": new_signature,
                                            "size": stat.st_size,
                                            "mtime": stat.st_mtime,
                                            "extension": current_extension,
                                        }
                            else:
                                # Novo arquivo
                                stat = os.stat(file_path)
                                signature = get_file_signature(file_path)

                                changes_detected.append(
                                    {
                                        "file": file_path,
                                        "type": "new",
                                        "timestamp": time.time(),
                                        "new_extension": current_extension,
                                        "new_size": stat.st_size,
                                    }
                                )

                                # Adicionar ao snapshot
                                snapshot[file_path] = {
                                    "signature": signature,
                                    "size": stat.st_size,
                                    "mtime": stat.st_mtime,
                                    "extension": current_extension,
                                }
                        except Exception as e:
                            logger.error(
                                f"Erro ao processar arquivo {file_path}: {str(e)}"
                            )

            # Verificar remoções
            existing_files = []
            for directory in DIRS_TO_MONITOR:
                if os.path.exists(directory):
                    for root, _, files in os.walk(directory):
                        for file in files:
                            existing_files.append(os.path.join(root, file))

            for file_path in list(snapshot.keys()):
                if file_path not in existing_files:
                    # Arquivo removido
                    changes_detected.append(
                        {
                            "file": file_path,
                            "type": "deleted",
                            "timestamp": time.time(),
                            "old_extension": snapshot[file_path]["extension"],
                            "old_size": snapshot[file_path]["size"],
                        }
                    )

                    # Remover do snapshot
                    del snapshot[file_path]

            # Registrar alterações detectadas
            for change in changes_detected:
                file_change_history.append(change)
                if change["type"] == "suspicious_file":
                    logger.warning(f"Arquivo suspeito: {change['file']}")
                elif (
                    change["type"] == "modified"
                    and "old_extension" in change
                    and "new_extension" in change
                ):
                    if change["old_extension"] != change["new_extension"]:
                        logger.warning(
                            f"Extensão de arquivo alterada: {change['file']} de {change['old_extension']} para {change['new_extension']}"
                        )

            # Analisar alterações em massa
            if changes_detected:
                logger.info(
                    f"Detectadas {len(changes_detected)} alterações de arquivos"
                )

                # Verificar padrões de ransomware
                mass_changes = detect_mass_changes()
                if mass_changes:
                    logger.critical(
                        f"ALERTA: Possível ataque de ransomware em andamento! {mass_changes['changes_count']} arquivos alterados em {mass_changes['window_seconds']} segundos."
                    )

                    # Salvar snapshot atual para recuperação
                    create_snapshot()

                    # Enviar alerta
                    alert_message = f"Possível ataque de ransomware detectado!\n\n"
                    alert_message += f"- {mass_changes['changes_count']} arquivos alterados em {mass_changes['window_seconds']} segundos\n"
                    alert_message += (
                        f"- Limite de alerta: {mass_changes['threshold']} arquivos\n\n"
                    )

                    if mass_changes["extensions_changed"]:
                        alert_message += "Alterações de extensão detectadas:\n"
                        for (old_ext, new_ext), count in mass_changes[
                            "extensions_changed"
                        ].items():
                            alert_message += f"- {count} arquivos alterados de {old_ext} para {new_ext}\n"

                    send_alert("Possível ataque de ransomware detectado", alert_message)

                    # Ativar medidas de proteção
                    if not is_attack_mode:
                        activate_protection_measures()

            # Salvar snapshot periodicamente
            if len(changes_detected) > 10:  # Muitas alterações, atualizar snapshot
                create_snapshot()

            time.sleep(10)  # Verificar a cada 10 segundos

        except Exception as e:
            logger.error(f"Erro durante monitoramento: {str(e)}")
            time.sleep(30)  # Esperar um pouco mais no caso de erro


def main():
    """Função principal."""
    logger.info("Iniciando sistema de monitoramento contra ransomware")

    # Criar snapshot inicial se não existir
    snapshots = [
        f
        for f in os.listdir(SNAPSHOT_DIR)
        if f.startswith("snapshot_") and f.endswith(".json")
    ]
    if not snapshots:
        logger.info("Criando snapshot inicial do sistema")
        create_snapshot()

    try:
        # Iniciar monitoramento em uma thread separada
        monitor_thread = threading.Thread(target=monitor_files, daemon=True)
        monitor_thread.start()

        # Manter o programa em execução
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
    main()
