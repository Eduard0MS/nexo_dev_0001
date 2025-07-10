@ECHO OFF

REM Arquivo batch para documentação do Nexo (Windows)
REM Equivalente ao Makefile para sistemas Unix

pushd %~dp0

REM Variáveis
set SPHINXOPTS=
set SPHINXBUILD=sphinx-build
set SOURCEDIR=.
set BUILDDIR=_build
set DJANGO_MANAGE=python ..\manage.py

if "%1" == "" goto help

if "%1" == "help" (
	:help
	echo Sistema de documentação do Nexo
	echo.
	echo Comandos disponíveis:
	echo   html          Gerar documentação HTML
	echo   pdf           Gerar documentação PDF
	echo   epub          Gerar documentação EPUB
	echo   clean         Limpar arquivos de build
	echo   serve         Iniciar servidor de desenvolvimento
	echo   watch         Modo watch (rebuild automático)
	echo   install-deps  Instalar dependências
	echo   coverage      Relatório de cobertura
	echo   auto          Modo automático (Django command)
	goto end
)

if "%1" == "html" (
	echo 🔨 Gerando documentação HTML...
	%SPHINXBUILD% -b html %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\html
	if errorlevel 1 exit /b 1
	echo ✅ Documentação HTML gerada em %BUILDDIR%\html\
	goto end
)

if "%1" == "pdf" (
	echo 🔨 Gerando documentação PDF...
	%SPHINXBUILD% -b latex %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\latex
	if errorlevel 1 exit /b 1
	cd %BUILDDIR%\latex
	make.bat
	cd ..\..
	echo ✅ Documentação PDF gerada em %BUILDDIR%\latex\
	goto end
)

if "%1" == "epub" (
	echo 🔨 Gerando documentação EPUB...
	%SPHINXBUILD% -b epub %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\epub
	if errorlevel 1 exit /b 1
	echo ✅ Documentação EPUB gerada em %BUILDDIR%\epub\
	goto end
)

if "%1" == "clean" (
	echo 🗑️  Limpando arquivos de build...
	for /d %%i in (%BUILDDIR%\*) do rmdir /q /s "%%i"
	del /q /s %BUILDDIR%\*
	echo ✅ Arquivos limpos
	goto end
)

if "%1" == "serve" (
	echo 🌐 Iniciando servidor de desenvolvimento...
	cd %BUILDDIR%\html
	python -m http.server 8080
	goto end
)

if "%1" == "watch" (
	echo 👀 Iniciando modo watch...
	sphinx-autobuild %SOURCEDIR% %BUILDDIR%\html --port 8080 --open-browser
	goto end
)

if "%1" == "install-deps" (
	echo 📦 Instalando dependências de documentação...
	pip install -r ..\requirements-docs.txt
	echo ✅ Dependências instaladas
	goto end
)

if "%1" == "coverage" (
	echo 📊 Gerando relatório de cobertura...
	%SPHINXBUILD% -b coverage %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\coverage
	if errorlevel 1 exit /b 1
	echo ✅ Relatório gerado em %BUILDDIR%\coverage\
	goto end
)

if "%1" == "auto" (
	echo 🤖 Executando modo automático...
	%DJANGO_MANAGE% gerar_documentacao --acao auto --verbose
	goto end
)

if "%1" == "full-rebuild" (
	echo 🚀 Rebuild completo...
	call %0 clean
	call %0 install-deps
	call %0 auto
	call %0 html
	echo 🚀 Rebuild completo finalizado
	goto end
)

if "%1" == "linkcheck" (
	echo 🔗 Verificando links...
	%SPHINXBUILD% -b linkcheck %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\linkcheck
	if errorlevel 1 exit /b 1
	goto end
)

if "%1" == "django-create" (
	%DJANGO_MANAGE% gerar_documentacao --acao create --incluir-frontend --verbose
	goto end
)

if "%1" == "django-update" (
	%DJANGO_MANAGE% gerar_documentacao --acao update --incluir-frontend --verbose
	goto end
)

if "%1" == "django-delete" (
	%DJANGO_MANAGE% gerar_documentacao --acao delete
	goto end
)

if "%1" == "django-watch" (
	%DJANGO_MANAGE% gerar_documentacao --acao update --watch --port 8080
	goto end
)

echo Comando desconhecido: %1
echo Digite 'make help' para ver os comandos disponíveis

:end
popd 