import pandas as pd
from .models import UnidadeCargo, CargoSIORG
from decimal import Decimal

def processa_planilhas(file_hierarquia, file_estrutura_viva):
    # Leitura da planilha de hierarquia
    if file_hierarquia.name.endswith('.csv'):
        df_hierarquia = pd.read_csv(file_hierarquia, encoding="utf-8")
    else:
        df_hierarquia = pd.read_excel(file_hierarquia)

    # Leitura da planilha de estrutura viva
    if file_estrutura_viva.name.endswith('.csv'):
        df_estrutura_viva = pd.read_csv(file_estrutura_viva, encoding="utf-8")
    else:
        df_estrutura_viva = pd.read_excel(file_estrutura_viva)

    # Processar a planilha de hierarquia: remover metadados e renomear colunas
    df_hierarquia = df_hierarquia.iloc[3:].reset_index(drop=True)
    df_hierarquia.columns = ["Código", "Unidade Organizacional - Sigla"]
    df_hierarquia.dropna(inplace=True)
    df_hierarquia["Código"] = df_hierarquia["Código"].astype(str).str.strip()

    # Processar a planilha de estrutura viva sem alterar os demais dados
    if "Código Unidade" not in df_estrutura_viva.columns:
        raise KeyError("A coluna 'Código Unidade' não foi encontrada na planilha de estrutura viva.")
    df_estrutura_viva["Código Unidade"] = df_estrutura_viva["Código Unidade"].astype(str).str.strip()
    if "Categoria" in df_estrutura_viva.columns:
        df_estrutura_viva["Categoria"] = df_estrutura_viva["Categoria"].fillna(0).astype(int)
    if "Nível" in df_estrutura_viva.columns:
        df_estrutura_viva["Nível"] = df_estrutura_viva["Nível"].fillna(0).astype(int)

    # -------------------------------
    # Apenas para construir o campo "Grafo"
    # -------------------------------
    hierarquia_info = {}
    stack = []
    for _, row in df_hierarquia.iterrows():
        codigo = row["Código"]
        unidade = row["Unidade Organizacional - Sigla"]
        # Aqui a lógica calcula o nível para construir o grafo a partir da indentação;
        # ela não altera nenhum dado que será carregado no BD.
        nivel_hierarquico = (len(unidade) - len(unidade.lstrip())) // 5
        while len(stack) > nivel_hierarquico:
            stack.pop()
        if stack:
            grafo_val = f"{hierarquia_info[stack[-1]]['grafo']}-{codigo}"
        else:
            grafo_val = codigo
        stack.append(codigo)
        hierarquia_info[codigo] = {
            "grafo": grafo_val,
            "nivel_hierarquico": nivel_hierarquico,
            "deno_unidade": unidade.strip()
        }

    # Cria uma cópia dos dados originais da planilha de estrutura viva
    df_resultado = df_estrutura_viva.copy()

    # Atualiza (ou adiciona) as colunas necessárias
    df_resultado["Grafo"] = df_resultado["Código Unidade"].map(
        lambda code: hierarquia_info.get(code, {}).get("grafo", "")
    )
    df_resultado["Nível Hierárquico"] = df_resultado["Código Unidade"].map(
        lambda code: hierarquia_info.get(code, {}).get("nivel_hierarquico", 0)
    )
    df_resultado["Deno Unidade"] = df_resultado["Código Unidade"].map(
        lambda code: hierarquia_info.get(code, {}).get("deno_unidade", "")
    )
    
    # Garantir que todas as colunas necessárias existam
    colunas_padrao = {
        "Tipo Unidade": "",
        "Sigla Unidade": "",
        "Categoria Unidade": "",
        "Órgão/Entidade": "",
        "Tipo do Cargo": "",
        "Denominação": "",
        "Complemento Denominação": "",
        "Categoria": 0,
        "Nível": 0,
        "Quantidade": 0,
        "Sigla": ""
    }
    
    for coluna, valor_padrao in colunas_padrao.items():
        if coluna not in df_resultado.columns:
            df_resultado[coluna] = valor_padrao
    
    # IMPORTANTE: Filtra apenas os registros que possuem um Grafo válido
    # Esses são os registros que realmente fazem parte da estrutura do ministério
    df_resultado = df_resultado[df_resultado["Grafo"].str.strip() != ""]
    print(f"Total de registros após filtragem: {len(df_resultado)}")
            
    return df_resultado

def processa_organograma():
    """
    Processa os dados das unidades e cargos em uma estrutura de grafo organizacional.
    Retorna um dicionário com a estrutura hierárquica e informações financeiras.
    """
    # Buscar todos os cargos SIORG para referência de valores
    cargos_siorg = {
        f"{cargo.cargo}": {
            'valor': Decimal(cargo.valor.replace('R$ ', '').replace('.', '').replace(',', '.')),
            'unitario': cargo.unitario
        }
        for cargo in CargoSIORG.objects.all()
    }

    # Buscar todas as unidades - filtrando apenas as que têm grafo válido
    unidades = UnidadeCargo.objects.exclude(grafo__exact='').exclude(grafo__isnull=True)
    
    print(f"Total de unidades com grafo válido: {unidades.count()}")
    
    # Estrutura para armazenar o organograma
    organograma = {}
    
    # Primeiro passo: agrupar unidades por código de grafo
    unidades_por_grafo = {}
    for unidade in unidades:
        if not unidade.grafo or unidade.grafo.strip() == '':
            continue
        
        codigo_atual = unidade.grafo.split('-')[-1]
        if codigo_atual not in unidades_por_grafo:
            unidades_por_grafo[codigo_atual] = []
        unidades_por_grafo[codigo_atual].append(unidade)
    
    # Segundo passo: processar cada grupo de unidades
    for codigo_atual, grupo_unidades in unidades_por_grafo.items():
        # Ordenar unidades pelo nível do cargo (decrescente)
        grupo_unidades.sort(key=lambda x: x.nivel, reverse=True)
        
        # Usar a unidade com o cargo de maior nível
        unidade_principal = grupo_unidades[0]
        niveis = unidade_principal.grafo.split('-')
        
        # Informações do cargo
        cargo_info = {
            'tipo': unidade_principal.tipo_cargo,
            'categoria': unidade_principal.categoria,
            'nivel': unidade_principal.nivel,
            'quantidade': unidade_principal.quantidade
        }
        
        # Calcular valor do cargo
        cargo_key = f"{unidade_principal.tipo_cargo} {unidade_principal.categoria} {unidade_principal.nivel:02d}"
        if cargo_key in cargos_siorg:
            cargo_info['valor'] = cargos_siorg[cargo_key]['valor']
            cargo_info['pontos'] = cargos_siorg[cargo_key]['unitario']
        else:
            cargo_info['valor'] = Decimal('0.00')
            cargo_info['pontos'] = Decimal('0.00')
        
        # Criar ou atualizar entrada no organograma
        if codigo_atual not in organograma:
            organograma[codigo_atual] = {
                'codigo': codigo_atual,
                'denominacao': unidade_principal.denominacao_unidade,
                'nivel_hierarquico': unidade_principal.nivel_hierarquico,
                'cargos': [],
                'subordinados': [],
                'pai': niveis[-2] if len(niveis) > 1 else None
            }
        
        # Adicionar todos os cargos do mesmo código
        for unidade in grupo_unidades:
            cargo_info = {
                'tipo': unidade.tipo_cargo,
                'categoria': unidade.categoria,
                'nivel': unidade.nivel,
                'quantidade': unidade.quantidade
            }
            
            cargo_key = f"{unidade.tipo_cargo} {unidade.categoria} {unidade.nivel:02d}"
            if cargo_key in cargos_siorg:
                cargo_info['valor'] = cargos_siorg[cargo_key]['valor']
                cargo_info['pontos'] = cargos_siorg[cargo_key]['unitario']
            else:
                cargo_info['valor'] = Decimal('0.00')
                cargo_info['pontos'] = Decimal('0.00')
                
            organograma[codigo_atual]['cargos'].append(cargo_info)
        
        # Estabelecer relações hierárquicas
        if len(niveis) > 1:
            pai = niveis[-2]
            if pai in organograma and codigo_atual not in organograma[pai]['subordinados']:
                organograma[pai]['subordinados'].append(codigo_atual)
    
    return organograma

def estrutura_json_organograma():
    """
    Estrutura os dados das unidades e cargos em um formato JSON hierárquico.
    Retorna uma lista de unidades com seus cargos e valores.
    """
    from .models import UnidadeCargo, CargoSIORG
    from decimal import Decimal
    
    # Buscar todos os cargos SIORG para referência de valores
    cargos_siorg = {
        f"{cargo.cargo}": {
            'valor': Decimal(cargo.valor.replace('R$ ', '').replace('.', '').replace(',', '.')),
            'unitario': cargo.unitario
        }
        for cargo in CargoSIORG.objects.all()
    }
    
    # Buscar todas as unidades com grafo válido
    unidades = UnidadeCargo.objects.exclude(grafo__exact='').exclude(grafo__isnull=True)
    
    # Lista para armazenar todas as unidades processadas
    unidades_processadas = []
    
    # Processar cada unidade
    for unidade in unidades:
        # Calcular valores do cargo
        cargo_key = f"{unidade.tipo_cargo} {unidade.categoria} {unidade.nivel:02d}"
        cargo_siorg = cargos_siorg.get(cargo_key, {'valor': Decimal('0'), 'unitario': Decimal('0')})
        
        valor_unitario = cargo_siorg['valor']
        pontos = cargo_siorg['unitario']
        
        # Calcular totais
        quantidade = unidade.quantidade or 0
        gasto_total = valor_unitario * quantidade
        pontos_total = pontos * quantidade
        
        # Estrutura da unidade
        dados_unidade = {
            'tipo_unidade': unidade.tipo_unidade,
            'denominacao_unidade': unidade.denominacao_unidade,
            'codigo_unidade': unidade.codigo_unidade,
            'sigla': unidade.sigla_unidade,
            'tipo_cargo': unidade.tipo_cargo,
            'denominacao': unidade.denominacao,
            'categoria': unidade.categoria,
            'nivel': unidade.nivel,
            'quantidade': quantidade,
            'grafo': unidade.grafo,
            'valor_unitario': float(valor_unitario),
            'pontos': float(pontos),
            'gasto_total': float(gasto_total),
            'pontos_total': float(pontos_total)
        }
        
        unidades_processadas.append(dados_unidade)
    
    return unidades_processadas

def processa_json_organograma(json_data):
    """
    Processa os dados do arquivo JSON do organograma e combina com os dados do SIORG.
    Retorna uma estrutura hierárquica com informações detalhadas de cada unidade.
    """
    from .models import CargoSIORG
    from decimal import Decimal
    import json
    
    # Carregar dados do SIORG para referência
    cargos_siorg = {
        f"{cargo.cargo}": {
            'valor': Decimal(cargo.valor.replace('R$ ', '').replace('.', '').replace(',', '.')),
            'unitario': cargo.unitario
        }
        for cargo in CargoSIORG.objects.all()
    }
    
    def calcula_valores_unidade(unidade_data):
        """Calcula os valores totais de uma unidade"""
        cargo_key = f"{unidade_data.get('tipo_cargo', '')} {unidade_data.get('categoria', '')} {unidade_data.get('nivel', ''):02d}"
        cargo_info = cargos_siorg.get(cargo_key, {'valor': Decimal('0'), 'unitario': Decimal('0')})
        
        quantidade = unidade_data.get('quantidade', 0)
        valor_total = cargo_info['valor'] * quantidade
        pontos_total = cargo_info['unitario'] * quantidade
        
        return {
            'valor_total': float(valor_total),
            'pontos_total': float(pontos_total),
            'valor_unitario': float(cargo_info['valor']),
            'pontos_unitario': float(cargo_info['unitario'])
        }
    
    def processa_unidade(unidade_data):
        """Processa uma unidade e seus subordinados recursivamente"""
        valores = calcula_valores_unidade(unidade_data)
        
        dados_unidade = {
            'id': unidade_data.get('id'),
            'codigo': unidade_data.get('codigo_unidade'),
            'nome': unidade_data.get('denominacao_unidade'),
            'sigla': unidade_data.get('sigla_unidade', ''),
            'cargo': {
                'tipo': unidade_data.get('tipo_cargo', ''),
                'categoria': unidade_data.get('categoria', 0),
                'nivel': unidade_data.get('nivel', 0),
                'quantidade': unidade_data.get('quantidade', 0),
                'valor_unitario': valores['valor_unitario'],
                'pontos_unitario': valores['pontos_unitario']
            },
            'valores': {
                'valor_total': valores['valor_total'],
                'pontos_total': valores['pontos_total']
            },
            'children': []
        }
        
        # Processar unidades subordinadas
        for subordinado in unidade_data.get('subordinados', []):
            sub_dados = processa_unidade(subordinado)
            dados_unidade['children'].append(sub_dados)
            # Somar valores dos subordinados
            dados_unidade['valores']['valor_total'] += sub_dados['valores']['valor_total']
            dados_unidade['valores']['pontos_total'] += sub_dados['valores']['pontos_total']
        
        return dados_unidade
    
    # Processar todo o organograma
    try:
        if isinstance(json_data, str):
            dados = json.loads(json_data)
        else:
            dados = json_data
            
        return processa_unidade(dados)
    except Exception as e:
        print(f"Erro ao processar JSON do organograma: {str(e)}")
        return None
