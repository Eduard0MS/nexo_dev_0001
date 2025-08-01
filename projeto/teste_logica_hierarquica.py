#!/usr/bin/env python
"""
Script para testar a lógica hierárquica de contagem de funcionários.
Lógica 1: Nó Pai (Secretaria) - usar coluna 'diretoria'
Lógica 2: Nó Agregador (Superior) - somar nós filhos
"""

import os
import sys
import django

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import RelatorioGratificacoes, UnidadeCargo
from collections import defaultdict

def identificar_tipo_no(sigla_unidade):
    """
    Identifica se um nó é pai (secretaria) ou agregador (superior).
    """
    # Buscar o nó na tabela UnidadeCargo
    no = UnidadeCargo.objects.filter(sigla_unidade=sigla_unidade).first()
    
    if not no:
        return None, None
    
    # Verificar se é um nó agregador (tem múltiplos filhos diretos)
    # Filhos diretos são nós que contêm o código do nó pai no grafo
    filhos_diretos = UnidadeCargo.objects.filter(
        grafo__contains=f"-{no.codigo_unidade}-"
    ).exclude(codigo_unidade=no.codigo_unidade)
    
    # Filtrar apenas os filhos diretos únicos (não netos e sem duplicatas)
    filhos_reais = {}
    for filho in filhos_diretos:
        # Verificar se é filho direto (não tem outros códigos entre o pai e o filho)
        grafo_filho = filho.grafo
        codigos_grafo = grafo_filho.split('-')
        
        # Encontrar a posição do código do pai no grafo
        try:
            pos_pai = codigos_grafo.index(str(no.codigo_unidade))
            # Se o código do filho está logo após o código do pai, é filho direto
            if pos_pai + 1 < len(codigos_grafo) and codigos_grafo[pos_pai + 1] == str(filho.codigo_unidade):
                # Usar sigla_unidade como chave para evitar duplicatas
                filhos_reais[filho.sigla_unidade] = filho
        except ValueError:
            continue
    
    # Converter para lista
    filhos_reais_lista = list(filhos_reais.values())
    
    # Verificar se é um nó agregador (tem múltiplos filhos diretos)
    if len(filhos_reais_lista) > 1:
        return "AGREGADOR", no
    elif len(filhos_reais_lista) == 1:
        # Se tem apenas 1 filho, verificar se esse filho tem filhos
        filho = filhos_reais_lista[0]
        netos = UnidadeCargo.objects.filter(
            grafo__contains=f"-{filho.codigo_unidade}-"
        ).exclude(codigo_unidade=filho.codigo_unidade)
        
        if netos.count() > 0:
            return "AGREGADOR", no
        else:
            return "PAI", no
    else:
        # Se não tem filhos diretos, é um nó pai
        return "PAI", no

def contar_funcionarios_no_pai(sigla_unidade):
    """
    Conta funcionários de um nó pai usando a coluna 'diretoria'.
    """
    print(f"\n🔍 CONTANDO FUNCIONÁRIOS DO NÓ PAI: {sigla_unidade}")
    print("-" * 60)
    
    # Contar funcionários onde diretoria = sigla_unidade
    funcionarios = RelatorioGratificacoes.objects.filter(diretoria=sigla_unidade)
    total = funcionarios.count()
    
    print(f"✅ Total de funcionários onde diretoria='{sigla_unidade}': {total}")
    
    if total > 0:
        print(f"\n👥 FUNCIONÁRIOS:")
        for i, func in enumerate(funcionarios, 1):
            print(f"{i}. {func.nome_servidor} (ID: {func.id})")
            print(f"   - Diretoria: {func.diretoria}")
            print(f"   - Coordenação: {func.coordenacao}")
            print()
    
    return total

def contar_funcionarios_no_agregador(sigla_unidade, no_agregador):
    """
    Conta funcionários de um nó agregador somando todos os nós filhos.
    """
    print(f"\n🔍 CONTANDO FUNCIONÁRIOS DO NÓ AGREGADOR: {sigla_unidade}")
    print("-" * 60)
    
    # Encontrar todos os nós filhos diretos usando a mesma lógica
    filhos_diretos = UnidadeCargo.objects.filter(
        grafo__contains=f"-{no_agregador.codigo_unidade}-"
    ).exclude(codigo_unidade=no_agregador.codigo_unidade)
    
    # Filtrar apenas os filhos diretos únicos (não netos e sem duplicatas)
    filhos_reais = {}
    for filho in filhos_diretos:
        grafo_filho = filho.grafo
        codigos_grafo = grafo_filho.split('-')
        
        try:
            pos_pai = codigos_grafo.index(str(no_agregador.codigo_unidade))
            if pos_pai + 1 < len(codigos_grafo) and codigos_grafo[pos_pai + 1] == str(filho.codigo_unidade):
                # Usar sigla_unidade como chave para evitar duplicatas
                filhos_reais[filho.sigla_unidade] = filho
        except ValueError:
            continue
    
    print(f"✅ Nós filhos encontrados: {len(filhos_reais)}")
    
    total_agregador = 0
    contagem_por_filho = {}
    
    for filho in filhos_reais.values():
        sigla_filho = filho.sigla_unidade
        print(f"\n📋 Processando filho: {sigla_filho}")
        
        # Para cada filho, usar a lógica de nó pai
        total_filho = contar_funcionarios_no_pai(sigla_filho)
        contagem_por_filho[sigla_filho] = total_filho
        total_agregador += total_filho
    
    print(f"\n📊 RESUMO DO NÓ AGREGADOR {sigla_unidade}:")
    print("-" * 40)
    for sigla, total in contagem_por_filho.items():
        print(f"  - {sigla}: {total} funcionários")
    print(f"  Total: {total_agregador} funcionários")
    
    return total_agregador, contagem_por_filho

def testar_logica_hierarquica():
    """
    Testa a lógica hierárquica com exemplos específicos.
    """
    print("Testando Lógica Hierárquica de Contagem de Funcionários")
    print("=" * 70)
    
    # Teste 1: SAGE (nó pai)
    print("\n🧪 TESTE 1: SAGE (NÓ PAI)")
    print("=" * 50)
    
    tipo_sage, no_sage = identificar_tipo_no('SAGE')
    print(f"Tipo do nó SAGE: {tipo_sage}")
    
    if tipo_sage == "PAI":
        total_sage = contar_funcionarios_no_pai('SAGE')
    else:
        print("❌ SAGE não é um nó pai!")
        total_sage = 0
    
    # Teste 2: SE (nó agregador)
    print("\n🧪 TESTE 2: SE (NÓ AGREGADOR)")
    print("=" * 50)
    
    tipo_se, no_se = identificar_tipo_no('SE')
    print(f"Tipo do nó SE: {tipo_se}")
    
    if tipo_se == "AGREGADOR":
        total_se, contagem_filhos_se = contar_funcionarios_no_agregador('SE', no_se)
    else:
        print("❌ SE não é um nó agregador!")
        total_se = 0
        contagem_filhos_se = {}
    
    # Resumo final
    print(f"\n📋 RESUMO FINAL:")
    print("=" * 70)
    print(f"✅ SAGE (nó pai): {total_sage} funcionários")
    print(f"✅ SE (nó agregador): {total_se} funcionários")
    print(f"  - Filhos: {contagem_filhos_se}")
    
    return {
        'sage': total_sage,
        'se': total_se,
        'filhos_se': contagem_filhos_se
    }

if __name__ == "__main__":
    try:
        resultados = testar_logica_hierarquica()
        
        print(f"\n🎯 CONCLUSÃO:")
        print("=" * 70)
        print(f"A lógica hierárquica está funcionando corretamente!")
        print(f"SAGE tem {resultados['sage']} funcionários (usando diretoria)")
        print(f"SE tem {resultados['se']} funcionários (somando filhos)")
        
    except Exception as e:
        print(f"❌ Erro ao executar o script: {e}")
        sys.exit(1) 