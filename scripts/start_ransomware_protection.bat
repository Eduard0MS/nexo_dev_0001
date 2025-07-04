@echo off
echo Iniciando proteção contra ransomware para Nexo...

REM Definir o diretório base
set BASE_DIR=%~dp0..

REM Verificar se os diretórios de backup existem
if not exist "%BASE_DIR%\backups" mkdir "%BASE_DIR%\backups"
if not exist "%BASE_DIR%\backups\snapshots" mkdir "%BASE_DIR%\backups\snapshots"
if not exist "%BASE_DIR%\backups\quarantine" mkdir "%BASE_DIR%\backups\quarantine"
if not exist "%BASE_DIR%\logs" mkdir "%BASE_DIR%\logs"

REM Executar backup completo inicial
echo Realizando backup inicial completo...
python "%BASE_DIR%\scripts\backup.py" --full

REM Iniciar monitoramento contra ransomware
echo Iniciando sistema de monitoramento...
start "Nexo Ransomware Monitor" /min python "%BASE_DIR%\scripts\ransomware_monitor.py"

REM Criar tarefa agendada para backup diário
echo Configurando backup diário...
schtasks /create /tn "NexoBackupDiario" /tr "python %BASE_DIR%\scripts\backup.py --full" /sc daily /st 03:00 /ru SYSTEM /f

echo.
echo Sistema de proteção contra ransomware iniciado!
echo Os logs estão disponíveis em: %BASE_DIR%\logs
echo.
echo Para verificar o status do monitoramento, use: 
echo   tasklist | findstr "python"
echo.
pause 