#!/usr/bin/env python
"""
Script simplificado para calcular a média institucional baseada em funcionários do MPO.
Conta funcionários apenas quando há correspondência exata entre:
- core_unidadecargo.sigla_unidade 
- core_relatoriogratificacoes.coordenacao
"""

import os
import sys
import django
from decimal import Decimal
import re
from collections import defaultdict

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import UnidadeCargo, RelatorioGratificacoes, CargoSIORG


def calcular_media_institucional_simplificado():
    """
    Calcula a média institucional do MPO baseada em funcionários.
    Lógica simplificada: conta funcionários apenas quando há correspondência exata
    entre sigla_unidade e coordenacao.
    """
    print("Calculando média institucional do MPO (lógica simplificada)...")
    print("=" * 70)
    
    # 1. Carregar cargos SIORG para cálculo de pontos
    cargos_siorg_dict = {}
    try:
        for cs in CargoSIORG.objects.all():
            key1 = f"{cs.cargo}"
            key2 = f"{cs.cargo}".replace(" ", "")
            
            match = re.match(r"(\w+)\s+(\d+)\s+(\d+)", cs.cargo)
            if match:
                tipo, categoria, nivel_cargo = match.groups()
                key3 = f"{tipo}{categoria}{nivel_cargo}"
                key4 = f"{tipo}-{categoria}-{nivel_cargo}"
                
                cargos_siorg_dict[key1] = cs
                cargos_siorg_dict[key2] = cs
                cargos_siorg_dict[key3] = cs
                cargos_siorg_dict[key4] = cs
            else:
                cargos_siorg_dict[key1] = cs
                cargos_siorg_dict[key2] = cs
        print(f"✅ Carregados {len(cargos_siorg_dict)} cargos SIORG para referência")
    except Exception as e:
        print(f"❌ Erro ao carregar cargos SIORG: {str(e)}")
        return None
    
    # 2. Calcular pontos por unidade (baseado em UnidadeCargo)
    print("\n2. CALCULANDO PONTOS POR UNIDADE:")
    print("-" * 50)
    
    unidades_pontos = {}
    registros = UnidadeCargo.objects.all()
    
    for registro in registros:
        try:
            quantidade = int(registro.quantidade) if registro.quantidade else 0
            categoria = int(registro.categoria) if registro.categoria is not None else 1
            nivel_cargo = int(registro.nivel) if registro.nivel is not None else 0
            
            # Criar chaves para buscar no dicionário de cargos SIORG
            cargo_key = f"{registro.tipo_cargo} {categoria} {nivel_cargo:02d}"
            cargo_key_alt = f"{registro.tipo_cargo}{categoria}{nivel_cargo:02d}"
            
            cargo_siorg = None
            for key in [cargo_key, cargo_key_alt, cargo_key.replace(" ", "")]:
                if key in cargos_siorg_dict:
                    cargo_siorg = cargos_siorg_dict[key]
                    break
            
            pontos_registro = Decimal('0')
            if cargo_siorg:
                pontos = Decimal(str(cargo_siorg.unitario)) if cargo_siorg.unitario else Decimal('0')
                pontos_registro = pontos * quantidade
            else:
                pontos_registro = registro.pontos_total or Decimal('0')
            
            # Agrupar por unidade (usando sigla_unidade)
            sigla_unidade = registro.sigla_unidade or "SEM_SIGLA"
            if sigla_unidade not in unidades_pontos:
                unidades_pontos[sigla_unidade] = {
                    'pontos': Decimal('0'),
                    'denominacao': registro.denominacao_unidade or sigla_unidade
                }
            
            unidades_pontos[sigla_unidade]['pontos'] += pontos_registro
            
        except Exception as e:
            print(f"⚠️ Erro ao processar registro {registro.id}: {e}")
            continue
    
    print(f"✅ Calculados pontos para {len(unidades_pontos)} unidades")
    
    # 3. Contar funcionários por unidade (lógica simplificada)
    print("\n3. CONTANDO FUNCIONÁRIOS POR UNIDADE (LÓGICA SIMPLIFICADA):")
    print("-" * 70)
    
    # Obter todas as siglas únicas de UnidadeCargo
    siglas_unidades = set(UnidadeCargo.objects.values_list('sigla_unidade', flat=True).distinct())
    siglas_unidades.discard(None)  # Remover None
    siglas_unidades.discard('')    # Remover string vazia
    
    print(f"✅ Siglas únicas encontradas em UnidadeCargo: {len(siglas_unidades)}")
    
    # Obter todas as coordenações únicas de RelatorioGratificacoes
    coordenacoes = set(RelatorioGratificacoes.objects.values_list('coordenacao', flat=True).distinct())
    coordenacoes.discard(None)  # Remover None
    coordenacoes.discard('')    # Remover string vazia
    
    print(f"✅ Coordenações únicas encontradas em RelatorioGratificacoes: {len(coordenacoes)}")
    
    # Encontrar correspondências exatas
    correspondencias_exatas = siglas_unidades.intersection(coordenacoes)
    print(f"✅ Correspondências exatas encontradas: {len(correspondencias_exatas)}")
    
    # Contar funcionários para cada correspondência exata
    unidades_funcionarios = defaultdict(int)
    
    for coordenacao in correspondencias_exatas:
        if coordenacao:  # Verificar se não é None ou vazio
            # Contar funcionários com essa coordenação
            count = RelatorioGratificacoes.objects.filter(coordenacao=coordenacao).count()
            unidades_funcionarios[coordenacao] = count
            print(f"  - {coordenacao}: {count} funcionários")
    
    print(f"✅ Contados funcionários para {len(unidades_funcionarios)} unidades com correspondência exata")
    
    # 4. Calcular médias por unidade
    print("\n4. CALCULANDO MÉDIAS POR UNIDADE:")
    print("-" * 50)
    
    total_pontos = Decimal('0')
    total_funcionarios = 0
    unidades_medias = {}
    
    for sigla, dados in unidades_pontos.items():
        funcionarios_unidade = unidades_funcionarios.get(sigla, 0)
        pontos_unidade = dados['pontos']
        
        if funcionarios_unidade > 0:
            media_unidade = pontos_unidade / funcionarios_unidade
        else:
            media_unidade = Decimal('0')
        
        unidades_medias[sigla] = {
            'pontos': pontos_unidade,
            'funcionarios': funcionarios_unidade,
            'media': media_unidade,
            'denominacao': dados['denominacao']
        }
        
        total_pontos += pontos_unidade
        total_funcionarios += funcionarios_unidade
    
    # 5. Calcular média institucional
    if total_funcionarios > 0:
        media_institucional = total_pontos / total_funcionarios
    else:
        media_institucional = Decimal('0')
    
    # 6. Calcular IEE para cada unidade
    print("\n5. CALCULANDO IEE POR UNIDADE:")
    print("-" * 50)
    
    for sigla, dados in unidades_medias.items():
        if media_institucional > 0:
            iee = dados['media'] / media_institucional
        else:
            iee = Decimal('0')
        
        dados['iee'] = iee
        
        if dados['funcionarios'] > 0:
            status = "Acima da média" if iee > 1 else "Na média" if iee == 1 else "Abaixo da média"
            print(f"{sigla}: {dados['pontos']:.2f} pontos, {dados['funcionarios']} funcionários, "
                  f"média {dados['media']:.4f}, IEE {iee:.4f} ({status})")
    
    # 7. Resultados finais
    print(f"\nRESULTADOS FINAIS:")
    print("=" * 70)
    print(f"Total de pontos do MPO: {total_pontos:.2f}")
    print(f"Total de funcionários do MPO: {total_funcionarios}")
    print(f"Média institucional: {media_institucional:.4f}")
    print(f"Unidades processadas: {len(unidades_medias)}")
    print(f"Unidades com funcionários: {len([u for u in unidades_medias.values() if u['funcionarios'] > 0])}")
    
    # 8. Estatísticas detalhadas
    print(f"\nESTATÍSTICAS DETALHADAS:")
    print("-" * 50)
    
    unidades_acima_media = sum(1 for dados in unidades_medias.values() if dados['iee'] > 1 and dados['funcionarios'] > 0)
    unidades_na_media = sum(1 for dados in unidades_medias.values() if dados['iee'] == 1 and dados['funcionarios'] > 0)
    unidades_abaixo_media = sum(1 for dados in unidades_medias.values() if dados['iee'] < 1 and dados['funcionarios'] > 0)
    
    print(f"Unidades acima da média: {unidades_acima_media}")
    print(f"Unidades na média: {unidades_na_media}")
    print(f"Unidades abaixo da média: {unidades_abaixo_media}")
    
    # Top 5 unidades com maior IEE (apenas com funcionários)
    print(f"\nTOP 5 UNIDADES COM MAIOR IEE:")
    print("-" * 50)
    unidades_com_funcionarios = [(sigla, dados) for sigla, dados in unidades_medias.items() if dados['funcionarios'] > 0]
    top_iee = sorted(unidades_com_funcionarios, key=lambda x: x[1]['iee'], reverse=True)[:5]
    for sigla, dados in top_iee:
        print(f"{sigla}: IEE {dados['iee']:.4f} ({dados['funcionarios']} funcionários)")
    
    # 9. Detalhamento das correspondências
    print(f"\nDETALHAMENTO DAS CORRESPONDÊNCIAS:")
    print("-" * 50)
    print(f"Total de siglas em UnidadeCargo: {len(siglas_unidades)}")
    print(f"Total de coordenações em RelatorioGratificacoes: {len(coordenacoes)}")
    print(f"Correspondências exatas: {len(correspondencias_exatas)}")
    print(f"Funcionários contados: {total_funcionarios}")
    
    return {
        'media_institucional': media_institucional,
        'total_pontos': total_pontos,
        'total_funcionarios': total_funcionarios,
        'unidades_processadas': len(unidades_medias),
        'unidades_medias': unidades_medias,
        'correspondencias_exatas': len(correspondencias_exatas)
    }


if __name__ == "__main__":
    try:
        resultados = calcular_media_institucional_simplificado()
        
        if resultados:
            print(f"\nRESUMO FINAL:")
            print("=" * 70)
            print(f"✅ Média Institucional do MPO: {resultados['media_institucional']:.4f}")
            print(f"✅ Total de Pontos do MPO: {resultados['total_pontos']:.2f}")
            print(f"✅ Total de Funcionários do MPO: {resultados['total_funcionarios']}")
            print(f"✅ Unidades Processadas: {resultados['unidades_processadas']}")
            print(f"✅ Correspondências Exatas: {resultados['correspondencias_exatas']}")
        
    except Exception as e:
        print(f"❌ Erro ao executar o script: {e}")
        sys.exit(1) 