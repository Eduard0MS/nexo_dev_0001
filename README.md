# Nexo - Sistema de Gestão

Este repositório contém o projeto Nexo Dev, uma solução para automatização de tarefas relacionadas ao gerenciamento de organogramas e cargos.

## Estrutura do Projeto

- `/nexo/`: Contém os módulos principais do projeto
- `/nexo/core/scripts/`: Scripts de automação para tarefas específicas

## Arquivos Principais

- `resultado_pontos_cargos.json`: Arquivo com pontuações de cargos
- `resultado_teste.txt`: Resultados de testes de funcionalidades

## Instalação e Configuração Completa (Passo a Passo)

```bash
# Clone o repositório
git clone https://github.com/Eduard0MS/nexo_dev_0001.git

# Entre no diretório do projeto
cd nexo_dev_0001

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
# source venv/bin/activate

# Navegue até o diretório da aplicação Django
cd nexo_dev/nexo

# Instale as dependências
pip install -r requirements.txt

# Esta etapa instalará todas as dependências necessárias, incluindo:
# - Django
# - django-allauth (para autenticação social)
# - django-crispy-forms
# - mysqlclient (para MySQL)
# - Pillow (para campos de imagem)
# - cryptography
# - python-dotenv
# entre outros pacotes
```

## Configuração do ambiente

1. Crie um arquivo `.env` na pasta `nexo_dev/nexo` com o seguinte conteúdo:

```
# Configurações do Banco de Dados
DB_ENGINE=django.db.backends.mysql
DB_NAME=nexo_dev
DB_USER=root
DB_PASSWORD=sua_senha_mysql
DB_HOST=127.0.0.1
DB_PORT=3306

# Ambiente
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=django-insecure-sua-chave-secreta-aqui

# Configurações de Autenticação Social
GOOGLE_CLIENT_ID=seu_id_do_cliente
GOOGLE_CLIENT_SECRET=seu_segredo_do_cliente
MICROSOFT_CLIENT_ID=SEU_MICROSOFT_CLIENT_ID_AQUI
MICROSOFT_CLIENT_SECRET=SEU_MICROSOFT_CLIENT_SECRET_AQUI
```

> ⚠️ **Importante**: O arquivo `.env` contém informações sensíveis e está incluído no `.gitignore` para não ser enviado ao repositório. Cada desenvolvedor deve criar seu próprio arquivo `.env` localmente.

2. Configure o banco de dados MySQL:

```bash
# Crie o banco de dados MySQL
mysql -u root -p
CREATE DATABASE nexo_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit
```

3. Execute as migrações para criar as tabelas no banco de dados:

```bash
python manage.py migrate
```

4. Crie um superusuário para acessar o painel administrativo:

```bash
python manage.py createsuperuser
```

5. Inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

## Configuração do Google SSO (Passo a Passo)

Para configurar a autenticação via Google, siga estes passos:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione um existente
3. Na barra lateral, navegue até "APIs e Serviços" > "Credenciais"
4. Clique em "Criar Credenciais" e selecione "ID do Cliente OAuth"
5. Configure o tipo de aplicação como "Aplicativo da Web"
6. Adicione os seguintes URIs de redirecionamento:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`
7. Clique em "Criar"
8. Copie o "ID do Cliente" e o "Segredo do Cliente"
9. Adicione esses valores ao seu arquivo `.env`:
   ```
   GOOGLE_CLIENT_ID=seu_id_do_cliente
   GOOGLE_CLIENT_SECRET=seu_segredo_do_cliente
   ```

## Troubleshooting

### Problema: Erro na conexão MySQL
Se você encontrar problemas ao conectar ao MySQL, verifique:
- Se o servidor MySQL está em execução
- Se as credenciais no arquivo `.env` estão corretas
- Se o banco de dados `nexo_dev` existe

### Problema: Erro nas migrações
Se as migrações falharem:
```bash
# Tente resetar as migrações
python manage.py migrate --fake-initial
# Ou crie um novo banco de dados e execute as migrações novamente
```

### Problema: Erros com o OAuth do Google
Se o login com Google não funcionar:
- Verifique se o ID do Cliente e o Segredo foram configurados corretamente no `.env`
- Certifique-se de que as URIs de redirecionamento estão corretas no Console do Google
- Verifique se a API OAuth está habilitada no projeto do Google

### Problema: Erro "No module named X"
O erro indica que falta uma dependência:
```bash
# Instalar a dependência individual
pip install nome_do_pacote

# Ou reinstalar todas as dependências 
pip install -r requirements.txt
```

### Problema: Erro "Cannot encode None for key 'client_id'"
Significa que as credenciais do OAuth não estão configuradas:
- Verifique se o arquivo `.env` existe e contém as credenciais corretas
- Certifique-se que o código está carregando o arquivo `.env` corretamente
- Tente reiniciar o servidor para garantir que as variáveis foram carregadas

### Problema: Erro "Duplicate entry for key 'auth_user.username'"
Este erro ocorre quando o adaptador social tenta criar um usuário sem um nome de usuário válido:
- Verifique as configurações em `settings.py` para garantir que `ACCOUNT_USERNAME_REQUIRED = True`
- Confirme que o adaptador social em `core/adapters.py` está definindo usernames únicos

## Registro de Alterações (Changelog)

### 2025-05-14: Correções na autenticação e dependências
- **Corrigido**: Problema de login social via Google OAuth
- **Adicionado**: Configuração do arquivo `.env` para variáveis de ambiente
- **Corrigido**: Tratamento de usernames no adaptador social para evitar duplicatas
- **Adicionado**: Instalação de dependências adicionais:
  - `django-allauth`: Para autenticação social
  - `python-dotenv`: Para carregar variáveis de ambiente
  - `cryptography`: Para funções criptográficas necessárias no OAuth
  - `Pillow`: Para processamento de imagens
  - `mysqlclient`: Conector MySQL para Django

### Alterações no adaptador social
Foram feitas melhorias no `CustomSocialAccountAdapter` para:
- Garantir que todos os usuários tenham usernames únicos
- Associar contas sociais com usuários existentes pelo email
- Redirecionar corretamente após o login
- Evitar o erro "Duplicate entry for key 'auth_user.username'"

### Configurações sensíveis
As credenciais e configurações sensíveis foram movidas para um arquivo `.env` que:
- Mantém segredos fora do controle de versão (via `.gitignore`)
- Facilita a configuração em diferentes ambientes (dev/prod)
- Centraliza todas as variáveis de configuração

## Scripts Utilitários

O projeto inclui vários scripts úteis:
- `clean_db.py`: Limpa o banco de dados
- `reset_db.py`: Reseta o banco de dados
- `setup_social_app.py`: Configura a aplicação social
- `fix_indentation.py`: Corrige a indentação dos arquivos
- `inspect_db.py`: Inspeciona o banco de dados

## Estrutura do Projeto

- `core/`: Aplicação principal
- `Nexus/`: Configurações do projeto Django
- Scripts utilitários na raiz do projeto

## Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request 

## Criação e Configuração de Administradores

### Criando um Superusuário (Admin)

O Django possui um poderoso painel de administração integrado. Para acessá-lo, você precisa criar um superusuário:

```bash
# Navegue até o diretório do projeto Django
cd nexo_dev/nexo

# Crie um superusuário
python manage.py createsuperuser
```

Siga as instruções do terminal:
- Digite o endereço de email
- Crie uma senha segura (deve conter pelo menos 8 caracteres)
- Confirme a senha

### Acessando o Painel de Administração

1. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

2. Acesse o painel de administração em seu navegador:
```
http://127.0.0.1:8000/admin/
```

3. Faça login com as credenciais do superusuário que você acabou de criar

### Configurando o Admin para Novos Modelos

Para adicionar seus próprios modelos ao painel de administração, edite o arquivo `admin.py` na aplicação correspondente:

```python
# Exemplo: core/admin.py
from django.contrib import admin
from .models import SeuModelo

@admin.register(SeuModelo)
class SeuModeloAdmin(admin.ModelAdmin):
    list_display = ('campo1', 'campo2', 'data_criacao')  # Campos exibidos na listagem
    search_fields = ('campo1', 'campo2')  # Campos pesquisáveis
    list_filter = ('campo3', 'status')  # Filtros laterais
    date_hierarchy = 'data_criacao'  # Navegação por hierarquia de data
    ordering = ('-data_criacao',)  # Ordenação padrão
    
    # Opcional: personalizar formulários de edição
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('campo1', 'campo2', 'campo3')
        }),
        ('Opções Avançadas', {
            'classes': ('collapse',),
            'fields': ('opcao1', 'opcao2'),
        }),
    )
```

### Personalizando a Aparência do Admin

Para personalizar a aparência e o comportamento do admin, você pode modificar seus templates:

1. Crie um diretório `templates/admin/` em seu projeto
2. Estenda os templates do admin que deseja personalizar

Exemplo para personalizar o cabeçalho e título:
```python
# No arquivo settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Certifique-se que este diretório está configurado
        'APP_DIRS': True,
        # ... resto da configuração
    },
]
```

```html
<!-- templates/admin/base_site.html -->
{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}{{ title }} | Nexo Dev Admin{% endblock %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        Nexo Dev - Painel Administrativo
    </a>
</h1>
{% endblock %}

{% block extrastyle %}
<style>
    #header {
        background: #2c3e50;
        color: white;
    }
    #header a:link, #header a:visited {
        color: white;
    }
</style>
{% endblock %}
```

### Gerenciando Usuários e Permissões

No painel de administração, você pode:

1. Criar novos usuários
2. Gerenciar grupos e permissões
3. Definir níveis de acesso específicos

Para criar um usuário com permissões limitadas:
1. Acesse "Usuários" no painel admin
2. Clique em "Adicionar usuário"
3. Preencha o email e senha
4. Na próxima tela, defina permissões específicas:
   - "Status da equipe" para acessar o admin
   - Escolha grupos específicos ou permissões individuais

### Dicas para o Admin em Produção

Para ambientes de produção, considere:

1. Proteger o acesso ao admin com HTTPS
2. Alterar a URL do admin para algo menos óbvio:
```python
# Em urls.py
urlpatterns = [
    path('gerenciamento-secreto/', admin.site.urls),  # URL personalizada em vez de 'admin/'
    # ... outras URLs
]
```

3. Limitar o acesso por IP:
```python
# Middleware personalizado para restringir acesso
from django.http import HttpResponseForbidden

class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        allowed_ips = ['192.168.1.100', '127.0.0.1']
        if request.path.startswith('/admin') and request.META['REMOTE_ADDR'] not in allowed_ips:
            return HttpResponseForbidden("Acesso não autorizado")
        return self.get_response(request)

# Adicione este middleware à lista MIDDLEWARE no settings.py
``` 

## Deploy Automático ✅
Sistema CI/CD com deploy automático configurado e funcionando - Última atualização: $(date)
