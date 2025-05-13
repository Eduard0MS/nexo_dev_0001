# Nexo

Este é um projeto Django que utiliza autenticação Google SSO e outras funcionalidades.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Ambiente virtual Python (venv)

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd nexo
```

2. Crie e ative um ambiente virtual:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas configurações.

5. Execute as migrações do banco de dados:
```bash
python manage.py migrate
```

6. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

O servidor estará disponível em `http://localhost:8000`

## Configuração do Google SSO

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google+ e configure as credenciais OAuth
4. Adicione as credenciais no arquivo `.env`

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