# 📚 Sistema CRUD de Documentação do Nexo

**Desenvolvido por:** Eduardo Moura da Silva  
**Equipe:** CGEST - SAGE/MPO  
**Repositório:** https://github.com/Eduard0MS/nexo_dev_0001  
**Status:** ✅ **FUNCIONANDO** - Sistema completamente implementado e testado!

## 🎯 Visão Geral

O Nexo agora possui um sistema completo de **CRUD (Create, Read, Update, Delete)** para documentação usando Sphinx com extensões avançadas. Este sistema permite:

- ✅ **CREATE**: Gerar documentação completa do zero
- ✅ **READ**: Visualizar documentação com **abertura automática no navegador**
- ✅ **UPDATE**: Atualizar documentação incrementalmente
- ✅ **DELETE**: Limpar arquivos de documentação

## 🚀 Como Usar

### ⚠️ Importante: Diretório Correto

Sempre execute os comandos a partir do diretório correto:

```bash
cd nexo_dev_0001\nexo_dev\nexo  # Windows
# ou
cd nexo_dev_0001/nexo_dev/nexo  # Linux/macOS
```

### 1. Instalação das Dependências

```bash
# Instalar dependências de documentação
pip install -r requirements-docs.txt
```

### 2. Comandos Principais

#### CREATE - Gerar Nova Documentação

```bash
# Gerar documentação completa
python manage.py gerar_documentacao --acao create --verbose

# Com frontend incluso
python manage.py gerar_documentacao --acao create --incluir-frontend --verbose

# Diferentes formatos
python manage.py gerar_documentacao --acao create --formato html
python manage.py gerar_documentacao --acao create --formato pdf
python manage.py gerar_documentacao --acao create --formato epub
```

#### READ - Visualizar Documentação (🆕 Abre Automaticamente!)

```bash
# Abrir documentação local no navegador (automático)
python manage.py gerar_documentacao --acao read

# Iniciar servidor local com abertura automática
python manage.py gerar_documentacao --acao read --servidor --port 8080

# Servidor em porta específica
python manage.py gerar_documentacao --acao read --servidor --port 3000
```

**🎉 Novidade**: O comando `--acao read` agora **abre automaticamente** a documentação no seu navegador padrão!

#### UPDATE - Atualizar Documentação

```bash
# Atualização incremental
python manage.py gerar_documentacao --acao update --verbose

# Modo watch (rebuild automático quando arquivos mudam)
python manage.py gerar_documentacao --acao update --watch --port 8080
```

#### DELETE - Limpar Documentação

```bash
# Remove arquivos de build
python manage.py gerar_documentacao --acao delete
```

#### AUTO - Modo Automático

```bash
# Detecta estado e age adequadamente
python manage.py gerar_documentacao --acao auto --verbose
```

### 3. Fluxo Completo Recomendado

```bash
# 1. Navegar para diretório correto
cd nexo_dev_0001\nexo_dev\nexo

# 2. Gerar documentação completa (primeira vez)
python manage.py gerar_documentacao --acao create --verbose

# 3. Abrir no navegador com servidor local
python manage.py gerar_documentacao --acao read --servidor --port 8080

# 4. Para atualizações futuras (mais rápido)
python manage.py gerar_documentacao --acao update --verbose
```

### 4. Usando Make/Batch

#### Linux/macOS

```bash
cd docs/
make auto           # Modo automático Django (recomendado)
make html           # Gerar HTML
make serve          # Servidor local
make watch          # Auto-rebuild
make clean          # Limpar
```

#### Windows

```cmd
cd docs\
make.bat auto       # Modo automático Django (recomendado)
make.bat html
make.bat serve
make.bat watch
make.bat clean
```

## 📁 Estrutura Atualizada

```
docs/
├── index.rst                  # ✅ Página principal (credenciais atualizadas)
├── conf.py                    # ✅ Configuração Sphinx (GitHub correto)
├── overview.rst               # ✅ Visão geral do sistema
├── installation.rst           # ✅ Guia de instalação
├── quickstart.rst            # ✅ Início rápido
├── guia-uso-documentacao.md   # ✅ Este guia
├── Makefile                   # ✅ Comandos Make Unix
├── make.bat                   # ✅ Comandos Batch Windows
├── _static/
│   └── custom.css             # ✅ Estilos personalizados
├── api/                       # 📖 Documentação da API
│   ├── models.rst             # ✅ Modelos Django
│   ├── views.rst              # ✅ Views
│   ├── auto_models.rst        # 🤖 Gerado automaticamente
│   └── auto_views.rst         # 🤖 Gerado automaticamente
└── _build/                    # 📦 Arquivos compilados
    └── html/                  # 🌐 Documentação HTML
```

## 🆕 Novas Funcionalidades

### Abertura Automática no Navegador

- **Arquivo local**: `python manage.py gerar_documentacao --acao read`
- **Servidor HTTP**: `python manage.py gerar_documentacao --acao read --servidor`
- **Porta personalizada**: `python manage.py gerar_documentacao --acao read --servidor --port 3000`

### Credenciais Atualizadas

- **Desenvolvedor**: Eduardo Moura da Silva
- **Equipe**: CGEST - SAGE/MPO  
- **Repositório**: https://github.com/Eduard0MS/nexo_dev_0001
- **Configuração GitHub**: Botões automáticos para editar/issues/downloads

### Detecção Inteligente

O sistema agora:

- ✅ Detecta se documentação existe antes de abrir
- ✅ Gera automaticamente se necessário
- ✅ Configura servidor HTTP com abertura automática
- ✅ Gerencia portas ocupadas
- ✅ Retorna ao diretório original sempre

## 🔧 Configurações Específicas

### Informações do Projeto

No `conf.py`:

```python
project = 'Nexo - Sistema de Gestão Organizacional'
copyright = '2025, Eduardo Moura da Silva - CGEST/SAGE/MPO'
author = 'Eduardo Moura da Silva'
```

### Repositório GitHub

```python
html_theme_options = {
    'repository_url': 'https://github.com/Eduard0MS/nexo_dev_0001',
    'path_to_docs': 'nexo_dev_0001/nexo_dev/nexo/docs/',
    'announcement': 'Sistema de Gestão Organizacional - CGEST/SAGE/MPO',
}
```

## 📞 Resolução de Problemas

### "can't open file manage.py"

**Problema**: Executando no diretório errado

**Solução**:
```bash
cd nexo_dev_0001\nexo_dev\nexo  # Windows
cd nexo_dev_0001/nexo_dev/nexo  # Linux/macOS
```

### "Address already in use"

**Problema**: Porta ocupada

**Solução**: 
```bash
# Usar porta diferente
python manage.py gerar_documentacao --acao read --servidor --port 9000
```

### Navegador não abre automaticamente

**Verificar**:
1. ✅ Comando executado no diretório correto
2. ✅ Documentação gerada (`_build/html/` existe)
3. ✅ Navegador padrão configurado no sistema

## 🎯 Exemplo Completo de Uso

```bash
# Terminal/PowerShell - Executar passo a passo

# 1. Navegar para diretório correto
C:\Users\eduardo.m.silva\nexo_dev_0001> cd nexo_dev_0001\nexo_dev\nexo

# 2. Instalar dependências (primeira vez)
PS C:\...\nexo_dev_0001\nexo_dev\nexo> pip install -r requirements-docs.txt

# 3. Gerar documentação completa
PS C:\...\nexo_dev_0001\nexo_dev\nexo> python manage.py gerar_documentacao --acao create --verbose

# 4. Abrir no navegador com servidor (AUTOMÁTICO!)
PS C:\...\nexo_dev_0001\nexo_dev\nexo> python manage.py gerar_documentacao --acao read --servidor --port 8080

# Resultado esperado:
# 🌐 Iniciando servidor HTTP...
# ✅ Servidor iniciado em: http://localhost:8080
# 🚀 Abrindo documentação em: http://localhost:8080
# 📖 Documentação aberta no navegador!
# ⏹️ Pressione Ctrl+C para parar o servidor
```

## ✅ Status Final de Implementação

| Funcionalidade | Status | Descrição |
|----------------|--------|-----------|
| CREATE | ✅ Funcionando | Gera documentação completa |
| READ | ✅ **Melhorado** | **Abertura automática no navegador** |
| UPDATE | ✅ Funcionando | Build incremental + watch |
| DELETE | ✅ Funcionando | Limpeza de arquivos |
| AUTO | ✅ Funcionando | Detecção automática |
| Multi-formato | ✅ Funcionando | HTML, PDF, EPUB |
| Frontend docs | ✅ Funcionando | Templates, CSS, JS |
| Credenciais | ✅ **Atualizado** | **Eduardo/CGEST-SAGE/MPO** |
| GitHub Config | ✅ **Atualizado** | **Eduard0MS/nexo_dev_0001** |
| Auto-navegador | 🆕 **NOVO** | **Abre automaticamente** |

---

**🎉 Sistema completamente funcional com abertura automática!**

Para testar agora mesmo:

```bash
cd nexo_dev_0001\nexo_dev\nexo
python manage.py gerar_documentacao --acao read --servidor --port 8080
```

A documentação será aberta automaticamente no seu navegador! 🚀 