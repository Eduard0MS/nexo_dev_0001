#!/usr/bin/env python3
"""
Script de teste para verificar o agrupamento de cargos idênticos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto.config.settings')
django.setup()

from projeto.apps.core.utils import estrutura_json_organograma_completa, _prepare_data_for_excel

def test_agrupamento():
    """
    Testa o agrupamento de cargos idênticos
    """
    print("=== TESTE DE AGRUPAMENTO DE CARGOS ===\n")
    
    # 1. Buscar dados do banco
    print("1. Buscando dados do banco...")
    try:
        dados_brutos = estrutura_json_organograma_completa()
        print(f"   ✅ Dados brutos obtidos: {len(dados_brutos)} registros")
    except Exception as e:
        print(f"   ❌ Erro ao buscar dados: {e}")
        return
    
    # 2. Verificar estrutura dos dados
    print("\n2. Verificando estrutura dos dados...")
    if dados_brutos:
        primeiro_item = dados_brutos[0]
        print(f"   Chaves disponíveis: {list(primeiro_item.keys())}")
        print(f"   Exemplo de item: {primeiro_item}")
    
    # 3. Verificar cargos idênticos nos dados brutos
    print("\n3. Verificando cargos idênticos nos dados brutos...")
    cargos_por_chave = {}
    for i, item in enumerate(dados_brutos):
        denominacao = item.get('denominacao', '')
        tipo_cargo = item.get('tipo_cargo', '')
        categoria = item.get('categoria', '')
        nivel = item.get('nivel', '')
        
        key = f"{denominacao}|{tipo_cargo}|{categoria}|{nivel}"
        
        if key not in cargos_por_chave:
            cargos_por_chave[key] = []
        cargos_por_chave[key].append({
            'index': i,
            'quantidade': item.get('quantidade', 0),
            'denominacao_unidade': item.get('denominacao_unidade', ''),
            'nivel_hierarquico': item.get('nivel_hierarquico', 0)
        })
    
    # Mostrar cargos que aparecem mais de uma vez
    cargos_repetidos = {k: v for k, v in cargos_por_chave.items() if len(v) > 1}
    print(f"   Cargos que aparecem mais de uma vez: {len(cargos_repetidos)}")
    
    for key, items in list(cargos_repetidos.items())[:5]:  # Mostrar apenas os primeiros 5
        print(f"   🔍 '{key}' aparece {len(items)} vezes:")
        for item in items:
            print(f"      - Índice {item['index']}: qty={item['quantidade']}, unidade='{item['denominacao_unidade']}', nivel={item['nivel_hierarquico']}")
    
    # 4. Testar função de agrupamento
    print("\n4. Testando função de agrupamento...")
    
    def _group_identical_cargos(items):
        """
        Função de agrupamento para teste
        """
        grouped = {}
        
        for item in items:
            denominacao = item.get('denominacao', '')
            tipo_cargo = item.get('tipo_cargo', '')
            categoria = item.get('categoria', '')
            nivel = item.get('nivel', '')
            
            key = f"{denominacao}|{tipo_cargo}|{categoria}|{nivel}"
            
            if key in grouped:
                grouped[key]['quantidade'] += item.get('quantidade', 0)
                print(f"      AGRUPOU: {key} - qty: {grouped[key]['quantidade']}")
            else:
                grouped[key] = item.copy()
                print(f"      NOVO: {key} - qty: {item.get('quantidade', 0)}")
        
        return list(grouped.values())
    
    # Testar com um subconjunto dos dados
    dados_teste = dados_brutos[:50]  # Primeiros 50 itens
    print(f"   Testando com {len(dados_teste)} itens...")
    
    dados_agrupados = _group_identical_cargos(dados_teste)
    print(f"   ✅ Após agrupamento: {len(dados_agrupados)} itens (era {len(dados_teste)})")
    
    # 5. Testar função completa de preparação
    print("\n5. Testando função completa de preparação...")
    try:
        dados_processados = _prepare_data_for_excel(dados_brutos[:100])  # Primeiros 100 itens
        print(f"   ✅ Dados processados: {len(dados_processados)} itens")
        
        # Verificar se há repetições nos dados processados
        print("   Verificando repetições nos dados processados...")
        processados_por_chave = {}
        for item in dados_processados:
            if item.get('denominacao'):  # Ignorar linhas vazias
                key = f"{item.get('denominacao', '')}|{item.get('cargo_formatado', '')}"
                if key not in processados_por_chave:
                    processados_por_chave[key] = []
                processados_por_chave[key].append(item)
        
        repetidos_processados = {k: v for k, v in processados_por_chave.items() if len(v) > 1}
        print(f"   Cargos repetidos nos dados processados: {len(repetidos_processados)}")
        
        for key, items in list(repetidos_processados.items())[:3]:
            print(f"   🔍 '{key}' aparece {len(items)} vezes:")
            for item in items:
                print(f"      - qty={item.get('quantidade', '')}, area='{item.get('area', '')}'")
    
    except Exception as e:
        print(f"   ❌ Erro ao processar dados: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== FIM DO TESTE ===")

if __name__ == "__main__":
    test_agrupamento() 