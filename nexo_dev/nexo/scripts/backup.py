#!/usr/bin/env python
"""
Script de backup automático com proteção contra ransomware.
Características:
- Backup do banco de dados
- Backup de arquivos de configuração
- Backup de dados de usuário
- Criptografia dos backups
- Logs detalhados
- Verificação de integridade
- Rotação de backups
"""

import os
import sys
import time
import shutil
import hashlib
import logging
import subprocess
import datetime
import gzip
import tarfile
from pathlib import Path
import traceback
import argparse
from dotenv import load_dotenv

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('backup')

# Carregar variáveis de ambiente
load_dotenv()

# Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = os.environ.get('BACKUP_DIR', os.path.join(BASE_DIR, 'backups'))
BACKUP_EXTERNAL_DIR = os.environ.get('BACKUP_EXTERNAL_DIR', '/mnt/external_backup')
BACKUP_CLOUD_DIR = os.environ.get('BACKUP_CLOUD_DIR', '/mnt/cloud_backup')

# Configurações de backup
MAX_LOCAL_BACKUPS = int(os.environ.get('MAX_LOCAL_BACKUPS', 7))  # 7 dias
MAX_EXTERNAL_BACKUPS = int(os.environ.get('MAX_EXTERNAL_BACKUPS', 30))  # 30 dias
MAX_CLOUD_BACKUPS = int(os.environ.get('MAX_CLOUD_BACKUPS', 60))  # 60 dias

# Configurações de criptografia
ENCRYPTION_KEY = os.environ.get('BACKUP_ENCRYPTION_KEY')
ENCRYPTION_ENABLED = ENCRYPTION_KEY is not None and ENCRYPTION_KEY != ''

# Configurações do banco de dados
DB_TYPE = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.environ.get('DB_NAME', 'db.sqlite3')
DB_USER = os.environ.get('DB_USER', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

def ensure_dir(directory):
    """Garante que o diretório existe."""
    os.makedirs(directory, exist_ok=True)
    logger.info(f"Diretório garantido: {directory}")

def get_timestamp():
    """Retorna um timestamp formatado para uso em nomes de arquivo."""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def calculate_checksum(filename):
    """Calcula o hash SHA-256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def backup_database():
    """Realiza o backup do banco de dados."""
    timestamp = get_timestamp()
    backup_filename = f"database_{timestamp}.sql.gz"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    logger.info(f"Iniciando backup do banco de dados para {backup_path}")
    
    try:
        if 'sqlite3' in DB_TYPE:
            # Para SQLite, fazemos uma cópia direta
            db_path = os.path.join(BASE_DIR, DB_NAME)
            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"Backup do SQLite concluído: {backup_path}")
        
        elif 'postgresql' in DB_TYPE:
            # Para PostgreSQL, usamos pg_dump
            cmd = [
                'pg_dump',
                '-h', DB_HOST,
                '-p', DB_PORT,
                '-U', DB_USER,
                '-d', DB_NAME,
                '--format=c',  # Custom format (comprimido)
                '-f', backup_path
            ]
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_PASSWORD
            
            process = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"Erro no pg_dump: {process.stderr}")
                raise Exception(f"Falha no backup do PostgreSQL: {process.stderr}")
            
            logger.info(f"Backup do PostgreSQL concluído: {backup_path}")
        
        else:
            logger.error(f"Tipo de banco de dados não suportado: {DB_TYPE}")
            raise Exception(f"Tipo de banco de dados não suportado: {DB_TYPE}")
        
        # Verificação de integridade
        checksum = calculate_checksum(backup_path)
        checksum_file = f"{backup_path}.sha256"
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Verificação de integridade concluída: {checksum}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Erro no backup do banco de dados: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def backup_config_files():
    """Realiza o backup dos arquivos de configuração."""
    timestamp = get_timestamp()
    backup_filename = f"config_{timestamp}.tar.gz"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    logger.info(f"Iniciando backup dos arquivos de configuração para {backup_path}")
    
    try:
        # Arquivos a serem incluídos no backup
        files_to_backup = [
            '.env',
            'Nexus/settings.py',
            'Nexus/wsgi.py',
            'Nexus/wsgi_prod.py',
            'gunicorn_config.py'
        ]
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for file in files_to_backup:
                file_path = os.path.join(BASE_DIR, file)
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=file)
                    logger.info(f"Adicionado ao backup: {file}")
                else:
                    logger.warning(f"Arquivo não encontrado: {file_path}")
        
        # Verificação de integridade
        checksum = calculate_checksum(backup_path)
        checksum_file = f"{backup_path}.sha256"
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Backup de configuração concluído: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Erro no backup de configuração: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def backup_user_data():
    """Realiza o backup de dados de usuário e uploads."""
    timestamp = get_timestamp()
    backup_filename = f"userdata_{timestamp}.tar.gz"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    logger.info(f"Iniciando backup de dados de usuário para {backup_path}")
    
    try:
        # Diretórios a serem incluídos no backup
        dirs_to_backup = [
            'media',      # Uploads de usuário
            'staticfiles',  # Arquivos estáticos gerados
        ]
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for dir_name in dirs_to_backup:
                dir_path = os.path.join(BASE_DIR, dir_name)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    tar.add(dir_path, arcname=dir_name)
                    logger.info(f"Adicionado ao backup: {dir_name}")
                else:
                    logger.warning(f"Diretório não encontrado: {dir_path}")
        
        # Verificação de integridade
        checksum = calculate_checksum(backup_path)
        checksum_file = f"{backup_path}.sha256"
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Backup de dados de usuário concluído: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Erro no backup de dados de usuário: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def encrypt_file(file_path):
    """Criptografa um arquivo usando GPG."""
    if not ENCRYPTION_ENABLED:
        logger.warning("Criptografia não configurada. Pulando etapa de criptografia.")
        return file_path
    
    logger.info(f"Iniciando criptografia de {file_path}")
    
    try:
        output_path = f"{file_path}.gpg"
        cmd = [
            'gpg',
            '--batch',
            '--yes',
            '--cipher-algo', 'AES256',
            '--symmetric',
            '--passphrase', ENCRYPTION_KEY,
            '--output', output_path,
            file_path
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Erro na criptografia: {process.stderr}")
            raise Exception(f"Falha na criptografia: {process.stderr}")
        
        # Após a criptografia bem-sucedida, podemos remover o arquivo original
        os.remove(file_path)
        os.remove(f"{file_path}.sha256")  # Também remove o arquivo de checksum
        
        logger.info(f"Criptografia concluída: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Erro na criptografia do arquivo: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def copy_to_external(file_path):
    """Copia o backup para armazenamento externo."""
    if not os.path.exists(BACKUP_EXTERNAL_DIR):
        logger.warning(f"Diretório externo não encontrado: {BACKUP_EXTERNAL_DIR}. Pulando backup externo.")
        return
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(BACKUP_EXTERNAL_DIR, filename)
    
    logger.info(f"Copiando backup para armazenamento externo: {dest_path}")
    
    try:
        shutil.copy2(file_path, dest_path)
        
        # Se há arquivo de checksum, copie também
        checksum_file = f"{file_path}.sha256"
        if os.path.exists(checksum_file):
            shutil.copy2(checksum_file, f"{dest_path}.sha256")
        
        logger.info(f"Backup externo concluído: {dest_path}")
    except Exception as e:
        logger.error(f"Erro ao copiar para armazenamento externo: {str(e)}")
        logger.error(traceback.format_exc())

def copy_to_cloud(file_path):
    """Copia o backup para armazenamento na nuvem."""
    if not os.path.exists(BACKUP_CLOUD_DIR):
        logger.warning(f"Diretório de nuvem não encontrado: {BACKUP_CLOUD_DIR}. Pulando backup na nuvem.")
        return
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(BACKUP_CLOUD_DIR, filename)
    
    logger.info(f"Copiando backup para armazenamento na nuvem: {dest_path}")
    
    try:
        shutil.copy2(file_path, dest_path)
        
        # Se há arquivo de checksum, copie também
        checksum_file = f"{file_path}.sha256"
        if os.path.exists(checksum_file):
            shutil.copy2(checksum_file, f"{dest_path}.sha256")
        
        logger.info(f"Backup na nuvem concluído: {dest_path}")
    except Exception as e:
        logger.error(f"Erro ao copiar para armazenamento na nuvem: {str(e)}")
        logger.error(traceback.format_exc())

def rotate_backups(directory, max_backups, file_prefix):
    """Remove backups antigos de acordo com a política de retenção."""
    if not os.path.exists(directory):
        logger.warning(f"Diretório não encontrado para rotação: {directory}")
        return
    
    logger.info(f"Iniciando rotação de backups em {directory} para {file_prefix}")
    
    try:
        # Lista todos os arquivos de backup com o prefixo especificado
        files = [f for f in os.listdir(directory) 
                if f.startswith(file_prefix) and (f.endswith('.gz') or f.endswith('.gpg'))]
        
        # Ordena por data (mais antigos primeiro)
        files.sort()
        
        # Remove os backups excedentes
        if len(files) > max_backups:
            for old_file in files[:-max_backups]:
                old_path = os.path.join(directory, old_file)
                os.remove(old_path)
                logger.info(f"Backup antigo removido: {old_path}")
                
                # Remover também o arquivo de checksum se existir
                checksum_file = f"{old_path}.sha256"
                if os.path.exists(checksum_file):
                    os.remove(checksum_file)
        
        logger.info(f"Rotação de backups concluída em {directory}")
    except Exception as e:
        logger.error(f"Erro durante a rotação de backups: {str(e)}")
        logger.error(traceback.format_exc())

def main():
    """Função principal que executa o backup completo."""
    parser = argparse.ArgumentParser(description='Backup do sistema Nexo')
    parser.add_argument('--full', action='store_true', help='Executa um backup completo (DB, config, dados)')
    parser.add_argument('--db', action='store_true', help='Executa apenas o backup do banco de dados')
    parser.add_argument('--config', action='store_true', help='Executa apenas o backup de configurações')
    parser.add_argument('--userdata', action='store_true', help='Executa apenas o backup de dados de usuário')
    args = parser.parse_args()
    
    # Se nenhuma opção for especificada, assume backup completo
    do_full = args.full or not (args.db or args.config or args.userdata)
    
    start_time = time.time()
    logger.info("Iniciando processo de backup")
    
    # Garantir que diretórios existam
    ensure_dir(BACKUP_DIR)
    
    try:
        # Backup do banco de dados
        if do_full or args.db:
            db_backup = backup_database()
            db_backup_enc = encrypt_file(db_backup) if ENCRYPTION_ENABLED else db_backup
            copy_to_external(db_backup_enc)
            copy_to_cloud(db_backup_enc)
            rotate_backups(BACKUP_DIR, MAX_LOCAL_BACKUPS, 'database_')
            rotate_backups(BACKUP_EXTERNAL_DIR, MAX_EXTERNAL_BACKUPS, 'database_')
            rotate_backups(BACKUP_CLOUD_DIR, MAX_CLOUD_BACKUPS, 'database_')
        
        # Backup de configurações
        if do_full or args.config:
            config_backup = backup_config_files()
            config_backup_enc = encrypt_file(config_backup) if ENCRYPTION_ENABLED else config_backup
            copy_to_external(config_backup_enc)
            copy_to_cloud(config_backup_enc)
            rotate_backups(BACKUP_DIR, MAX_LOCAL_BACKUPS, 'config_')
            rotate_backups(BACKUP_EXTERNAL_DIR, MAX_EXTERNAL_BACKUPS, 'config_')
            rotate_backups(BACKUP_CLOUD_DIR, MAX_CLOUD_BACKUPS, 'config_')
        
        # Backup de dados de usuário
        if do_full or args.userdata:
            userdata_backup = backup_user_data()
            userdata_backup_enc = encrypt_file(userdata_backup) if ENCRYPTION_ENABLED else userdata_backup
            copy_to_external(userdata_backup_enc)
            copy_to_cloud(userdata_backup_enc)
            rotate_backups(BACKUP_DIR, MAX_LOCAL_BACKUPS, 'userdata_')
            rotate_backups(BACKUP_EXTERNAL_DIR, MAX_EXTERNAL_BACKUPS, 'userdata_')
            rotate_backups(BACKUP_CLOUD_DIR, MAX_CLOUD_BACKUPS, 'userdata_')
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Backup concluído com sucesso em {duration:.2f} segundos")
        return 0
        
    except Exception as e:
        logger.error(f"Erro durante o processo de backup: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 