# 📊 Sistema de Gestão de Relatórios

## Visão Geral

O Sistema de Gestão de Relatórios foi desenvolvido para automatizar o processamento de planilhas Excel com dados de funcionários e estruturas organizacionais. O sistema permite upload, processamento automático e consulta dos dados através da interface administrativa do Django.

## 🗂️ Tipos de Relatórios Suportados

### 1. Gratificações e Lotações (`gratificacoes`)
Processa dados completos de funcionários incluindo:
- **Informações Pessoais**: Nome, Matrícula SIAPE, CPF, Data de Nascimento, Idade, Sexo
- **Dados Funcionais**: Situação Funcional, Cargo, Nível, Jornada de Trabalho
- **Gratificações**: GSISTE e GSISTE Nível
- **Funções**: Função, Nível da Função, Atividade da Função
- **Lotação**: Unidade de Lotação, Secretaria da Lotação, UF
- **Exercício**: UORG de Exercício, Unidade de Exercício, Coordenação, Diretoria, Secretaria
- **Hierarquia**: Órgão Origem, Dados do Chefe e Substituto
- **Contato**: e-Mail Institucional

**Estrutura esperada da planilha (29 colunas):**
```
1. Nome do Servidor
2. Matrícula SIAPE
3. CPF
4. Data de Nascimento
5. Idade
6. Sexo
7. Situação Funcional
8. Cargo
9. Nível
10. Gsiste
11. Gsiste Nível
12. Função
13. Nível da Função
14. Atividade da Função
15. Jornada de Trabalho
16. Unidade de Lotação
17. Secretaria da Lotação
18. UF
19. UORG de Exercício
20. Unidade de Exercício
21. Coordenação
22. Diretoria
23. Secretaria
24. Órgão Origem
25. e-Mail Institucional
26. Siape do Titular Chefe
27. CPF do Titular do Chefe
28. Siape do Substituto
29. CPF do Substituto
```

### 2. Órgãos Centrais e Setoriais (`orgaos`)
Processa informações sobre estrutura organizacional:
- Tipo de Órgão (Central/Setorial)
- Nível do Cargo
- Valor Máximo da GSISTE
- Data de Efeitos Financeiros

### 3. Efetivo de Funcionários (`efetivo`)
Processa dados de efetivo atual:
- QT (Número sequencial)
- Nome Completo
- Função
- Unidade Macro
- Horário
- Bloco/Andar

### 4. Facilities Assistente ADM (`facilities`)
Dados específicos de assistentes administrativos (usa a mesma estrutura do efetivo).

## 🚀 Como Usar

### Via Interface Admin

1. **Acesse o Admin**: `/admin/core/relatorio/`
2. **Adicionar Relatório**: Clique em "Adicionar Relatório"
3. **Preencher Dados**:
   - Nome: Nome identificador do relatório
   - Tipo: Selecione o tipo correto
   - Arquivo: Faça upload da planilha Excel
   - Descrição: (Opcional) Descrição do relatório
4. **Salvar**: O sistema salvará o relatório
5. **Processar**: Use a ação "Processar relatórios selecionados" ou aguarde o processamento automático
6. **Visualizar**: Clique em "Ver Estatísticas" para ver os dados processados

### Via Linha de Comando

```bash
python manage.py processar_relatorio \
    --arquivo /caminho/para/planilha.xlsx \
    --tipo gratificacoes \
    --nome "Relatório de Gratificações Janeiro 2024" \
    --descricao "Dados de gratificações do mês de janeiro" \
    --usuario admin
```

**Parâmetros:**
- `--arquivo`: Caminho para a planilha Excel
- `--tipo`: Tipo do relatório (gratificacoes, orgaos, efetivo, facilities, outro)
- `--nome`: Nome identificador
- `--descricao`: (Opcional) Descrição
- `--usuario`: (Opcional) Username do usuário responsável

## 🏗️ Estrutura Técnica

### Modelos (models.py)

#### `Relatorio`
Armazena informações sobre os arquivos de relatório:
- nome, tipo, arquivo, descrição
- data_upload, usuario_upload
- processado, data_processamento

#### `RelatorioGratificacoes`
Armazena dados processados de gratificações (29 campos).

#### `RelatorioOrgaosCentrais`
Armazena dados de órgãos centrais e setoriais.

#### `RelatorioEfetivo`
Armazena dados de efetivo de funcionários.

### Processamento (relatorio_processor.py)

#### `processar_relatorio(relatorio_obj)`
Função principal que:
1. Identifica o tipo de relatório
2. Chama a função específica de processamento
3. Retorna sucesso/erro e mensagem

#### `obter_estatisticas_relatorio(relatorio_obj)`
Gera estatísticas dos dados processados.

### Interface Admin (admin.py)

#### `RelatorioAdmin`
- Interface para upload e gestão de relatórios
- Action para processamento em lote
- View de estatísticas personalizadas
- Template customizado com cards visuais

## 📊 Estatísticas Disponíveis

### Para Gratificações:
- Total de funcionários
- Cargos únicos
- Unidades de lotação únicas

### Para Órgãos:
- Total de órgãos
- Órgãos centrais vs setoriais

### Para Efetivo:
- Total de funcionários
- Funções únicas
- Unidades únicas

## 🔧 Configuração

### Dependências
- pandas: Processamento de planilhas
- openpyxl: Leitura de arquivos Excel
- Django: Framework web

### Migrações
```bash
python manage.py makemigrations core
python manage.py migrate
```

### Permissões
- Usuários admin podem fazer upload e processar relatórios
- Dados são organizados por usuário responsável

## 📁 Estrutura de Arquivos

```
core/
├── models.py                 # Modelos de dados
├── admin.py                  # Interface administrativa
├── relatorio_processor.py    # Processamento de planilhas
├── management/
│   └── commands/
│       └── processar_relatorio.py  # Comando CLI
└── templates/
    └── admin/
        ├── relatorio_estatisticas.html      # Template de estatísticas
        └── core/relatorio/change_list.html  # Template da lista
```

## 🛡️ Tratamento de Erros

- **Arquivos inválidos**: Validação de formato Excel
- **Dados corrompidos**: Pula linhas com erro e continua processamento
- **Campos faltantes**: Campos opcionais tratam valores vazios
- **Tipos incompatíveis**: Conversão segura de tipos de dados

## 📈 Melhorias Futuras

- [ ] Export de dados processados para Excel/CSV
- [ ] Dashboard com gráficos e análises
- [ ] Notificações por email após processamento
- [ ] Histórico de alterações nos dados
- [ ] API REST para integração externa
- [ ] Processamento em background para arquivos grandes
- [ ] Validação de estrutura de planilhas antes do processamento

## 🆘 Troubleshooting

### Erro: "Tipo de relatório não suportado"
- Verifique se o tipo selecionado corresponde ao formato da planilha

### Erro: "Arquivo deve ser uma planilha Excel"
- Certifique-se de que o arquivo tem extensão .xlsx ou .xls

### Processamento parcial
- Verifique os logs para identificar linhas com problemas
- Dados válidos são processados mesmo com algumas linhas com erro

### Memória insuficiente
- Para planilhas muito grandes, use o comando CLI
- Considere dividir a planilha em arquivos menores 