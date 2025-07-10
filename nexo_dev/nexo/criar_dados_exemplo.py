#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexo.settings')
django.setup()

from core.models import Decreto
from datetime import date

def criar_decretos_exemplo():
    """Cria decretos de exemplo para teste"""
    
    # Limpar decretos existentes
    Decreto.objects.all().delete()
    
    # Criar decretos de exemplo
    decretos = [
        {
            'numero': 'Decreto nº 11.355/2022',
            'data_publicacao': date(2022, 12, 30),
            'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério do Planejamento e Orçamento',
            'tipo': 'estrutura_regimental',
            'status': 'vigente',
            'observacoes': 'Estrutura atual do MPO'
        },
        {
            'numero': 'Decreto nº 10.185/2019',
            'data_publicacao': date(2019, 12, 20),
            'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério da Economia',
            'tipo': 'estrutura_regimental',
            'status': 'revogado',
            'observacoes': 'Estrutura do antigo Ministério da Economia'
        },
        {
            'numero': 'Decreto nº 9.745/2019',
            'data_publicacao': date(2019, 4, 8),
            'titulo': 'Aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério do Planejamento, Desenvolvimento e Gestão',
            'tipo': 'estrutura_regimental',
            'status': 'revogado',
            'observacoes': 'Estrutura anterior do MPDG'
        },
        {
            'numero': 'Decreto nº 8.109/2013',
            'data_publicacao': date(2013, 9, 17),
            'titulo': 'Dispõe sobre a estrutura organizacional e as competências do Ministério do Planejamento, Orçamento e Gestão',
            'tipo': 'reorganizacao',
            'status': 'revogado',
            'observacoes': 'Estrutura anterior do MPOG'
        },
        {
            'numero': 'Decreto nº 10.438/2020',
            'data_publicacao': date(2020, 7, 1),
            'titulo': 'Altera o Decreto nº 10.185, de 20 de dezembro de 2019, que aprova a Estrutura Regimental e o Quadro Demonstrativo dos Cargos em Comissão e das Funções de Confiança do Ministério da Economia',
            'tipo': 'alteracao',
            'status': 'revogado',
            'observacoes': 'Alterações na estrutura do ME'
        }
    ]
    
    for decreto_data in decretos:
        Decreto.objects.create(**decreto_data)
    
    print(f'Criados {Decreto.objects.count()} decretos de exemplo')

if __name__ == '__main__':
    criar_decretos_exemplo()
    print('Dados de exemplo criados com sucesso!') 