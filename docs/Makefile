# Makefile para documentação do Nexo
# 
# Comandos disponíveis:
#   make html          - Gera documentação HTML
#   make pdf           - Gera documentação PDF
#   make clean         - Limpa arquivos de build
#   make serve         - Inicia servidor de desenvolvimento
#   make watch         - Modo watch (auto-rebuild)
#   make install-deps  - Instala dependências de documentação
#   make coverage      - Gera relatório de cobertura

# Variáveis
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
DJANGO_MANAGE = python ../manage.py

# Comandos principais
.PHONY: help html pdf epub clean serve watch install-deps coverage auto

help:
	@echo "Sistema de documentação do Nexo"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  html          Gerar documentação HTML"
	@echo "  pdf           Gerar documentação PDF"
	@echo "  epub          Gerar documentação EPUB"
	@echo "  clean         Limpar arquivos de build"
	@echo "  serve         Iniciar servidor de desenvolvimento"
	@echo "  watch         Modo watch (rebuild automático)"
	@echo "  install-deps  Instalar dependências"
	@echo "  coverage      Relatório de cobertura"
	@echo "  auto          Modo automático (Django command)"

html:
	@echo "🔨 Gerando documentação HTML..."
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "✅ Documentação HTML gerada em $(BUILDDIR)/html/"

pdf:
	@echo "🔨 Gerando documentação PDF..."
	$(SPHINXBUILD) -b latex $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/latex
	@cd $(BUILDDIR)/latex && make
	@echo "✅ Documentação PDF gerada em $(BUILDDIR)/latex/"

epub:
	@echo "🔨 Gerando documentação EPUB..."
	$(SPHINXBUILD) -b epub $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/epub
	@echo "✅ Documentação EPUB gerada em $(BUILDDIR)/epub/"

clean:
	@echo "🗑️  Limpando arquivos de build..."
	rm -rf $(BUILDDIR)/*
	@echo "✅ Arquivos limpos"

serve: html
	@echo "🌐 Iniciando servidor de desenvolvimento..."
	@cd $(BUILDDIR)/html && python -m http.server 8080

watch:
	@echo "👀 Iniciando modo watch..."
	sphinx-autobuild $(SOURCEDIR) $(BUILDDIR)/html --port 8080 --open-browser

install-deps:
	@echo "📦 Instalando dependências de documentação..."
	pip install -r ../requirements-docs.txt
	@echo "✅ Dependências instaladas"

coverage:
	@echo "📊 Gerando relatório de cobertura..."
	$(SPHINXBUILD) -b coverage $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/coverage
	@echo "✅ Relatório gerado em $(BUILDDIR)/coverage/"

auto:
	@echo "🤖 Executando modo automático..."
	$(DJANGO_MANAGE) gerar_documentacao --acao auto --verbose

# Comandos avançados
.PHONY: full-rebuild linkcheck deploy

full-rebuild: clean install-deps auto html
	@echo "🚀 Rebuild completo finalizado"

linkcheck:
	@echo "🔗 Verificando links..."
	$(SPHINXBUILD) -b linkcheck $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/linkcheck

deploy: full-rebuild
	@echo "🚀 Preparando para deploy..."
	@# Adicione aqui comandos específicos para deploy
	@echo "✅ Documentação pronta para deploy"

# Atalhos para comandos Django
.PHONY: django-create django-update django-delete

django-create:
	$(DJANGO_MANAGE) gerar_documentacao --acao create --incluir-frontend --verbose

django-update:
	$(DJANGO_MANAGE) gerar_documentacao --acao update --incluir-frontend --verbose

django-delete:
	$(DJANGO_MANAGE) gerar_documentacao --acao delete

django-watch:
	$(DJANGO_MANAGE) gerar_documentacao --acao update --watch --port 8080 