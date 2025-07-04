@echo off
echo Iniciando todos os testes do sistema Nexo...

REM Definir o diretório base
set BASE_DIR=%~dp0..

REM Verificar se os diretórios existem
if not exist "%BASE_DIR%\logs" mkdir "%BASE_DIR%\logs"

REM Executar todos os testes
python "%BASE_DIR%\scripts\run_all_tests.py"

echo.
echo Testes concluídos!
echo Os logs e relatórios estão disponíveis em: %BASE_DIR%\logs
echo.
pause 