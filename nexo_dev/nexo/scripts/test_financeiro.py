#!/usr/bin/env python
"""
Script para testar o sistema financeiro do Nexo.
Este script testa operações de lançamentos, relatórios e balanços financeiros.
"""

import os
import sys
import logging
import unittest
import django
import decimal
import datetime
from pathlib import Path
from django.db import transaction
from decimal import Decimal
from django.utils import timezone

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/financeiro_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('financeiro_test')

# Configurar ambiente Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')
django.setup()

# Importar modelos após configurar Django
from core.models import (
    PlanoContas, CategoriaFinanceira, ContaBancaria, 
    LancamentoFinanceiro, Fornecedor, Cliente
)

class FinanceiroTestCase(unittest.TestCase):
    """Classe de teste para funcionalidades do sistema financeiro."""
    
    def setUp(self):
        """Configuração para cada teste."""
        # Limpar dados existentes
        LancamentoFinanceiro.objects.all().delete()
        ContaBancaria.objects.all().delete()
        CategoriaFinanceira.objects.all().delete()
        PlanoContas.objects.all().delete()
        Fornecedor.objects.all().delete()
        Cliente.objects.all().delete()
        
        # Criar plano de contas
        self.plano_receitas = PlanoContas.objects.create(
            codigo="1",
            descricao="Receitas",
            tipo="R"  # Receita
        )
        
        self.plano_despesas = PlanoContas.objects.create(
            codigo="2",
            descricao="Despesas",
            tipo="D"  # Despesa
        )
        
        # Criar categorias de receitas
        self.cat_vendas = CategoriaFinanceira.objects.create(
            nome="Vendas",
            descricao="Receita de vendas de produtos/serviços",
            plano_contas=self.plano_receitas
        )
        
        self.cat_servicos = CategoriaFinanceira.objects.create(
            nome="Prestação de Serviços",
            descricao="Receita de serviços prestados",
            plano_contas=self.plano_receitas
        )
        
        # Criar categorias de despesas
        self.cat_fornecedores = CategoriaFinanceira.objects.create(
            nome="Fornecedores",
            descricao="Pagamento a fornecedores",
            plano_contas=self.plano_despesas
        )
        
        self.cat_folha = CategoriaFinanceira.objects.create(
            nome="Folha de Pagamento",
            descricao="Pagamento de salários",
            plano_contas=self.plano_despesas
        )
        
        self.cat_impostos = CategoriaFinanceira.objects.create(
            nome="Impostos",
            descricao="Pagamento de impostos e taxas",
            plano_contas=self.plano_despesas
        )
        
        # Criar contas bancárias
        self.conta_principal = ContaBancaria.objects.create(
            nome="Conta Principal",
            banco="Banco do Brasil",
            agencia="1234",
            numero="56789-0",
            tipo="CC",  # Conta Corrente
            saldo_inicial=Decimal("10000.00")
        )
        
        self.conta_investimentos = ContaBancaria.objects.create(
            nome="Conta Investimentos",
            banco="Caixa Econômica",
            agencia="5678",
            numero="12345-6",
            tipo="CP",  # Poupança
            saldo_inicial=Decimal("5000.00")
        )
        
        # Criar fornecedores
        self.fornecedor1 = Fornecedor.objects.create(
            nome="Fornecedor A Ltda",
            cnpj="12.345.678/0001-90",
            endereco="Rua A, 123",
            telefone="(11) 1234-5678",
            email="contato@fornecedora.com.br"
        )
        
        self.fornecedor2 = Fornecedor.objects.create(
            nome="Fornecedor B S/A",
            cnpj="98.765.432/0001-10",
            endereco="Av. B, 456",
            telefone="(11) 8765-4321",
            email="contato@fornecedorb.com.br"
        )
        
        # Criar clientes
        self.cliente1 = Cliente.objects.create(
            nome="Cliente X",
            tipo="PJ",  # Pessoa Jurídica
            documento="23.456.789/0001-12",
            endereco="Rua X, 789",
            telefone="(11) 2345-6789",
            email="contato@clientex.com.br"
        )
        
        self.cliente2 = Cliente.objects.create(
            nome="Cliente Y",
            tipo="PF",  # Pessoa Física
            documento="345.678.901-23",
            endereco="Av. Y, 987",
            telefone="(11) 3456-7890",
            email="clientey@email.com"
        )
        
        logger.info("Ambiente de teste financeiro configurado")
    
    def tearDown(self):
        """Limpeza após cada teste."""
        # Não apagamos os dados aqui para permitir inspeção manual após os testes
        pass
    
    def test_1_criar_lancamentos_receitas(self):
        """Teste de criação de lançamentos de receitas."""
        logger.info("Testando criação de lançamentos de receitas")
        
        # Criar lançamentos de receitas
        receita1 = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=Decimal("1500.00"),
            descricao="Venda de produtos para Cliente X",
            tipo="R",  # Receita
            categoria=self.cat_vendas,
            conta=self.conta_principal,
            cliente=self.cliente1,
            status="PG"  # Pago
        )
        
        receita2 = LancamentoFinanceiro.objects.create(
            data=timezone.now().date() + datetime.timedelta(days=1),
            valor=Decimal("2000.00"),
            descricao="Serviço de consultoria para Cliente Y",
            tipo="R",  # Receita
            categoria=self.cat_servicos,
            conta=self.conta_principal,
            cliente=self.cliente2,
            status="PG"  # Pago
        )
        
        # Verificações
        self.assertEqual(LancamentoFinanceiro.objects.filter(tipo="R").count(), 2)
        self.assertEqual(LancamentoFinanceiro.objects.filter(categoria=self.cat_vendas).count(), 1)
        self.assertEqual(LancamentoFinanceiro.objects.filter(categoria=self.cat_servicos).count(), 1)
        
        # Verificar valor total de receitas
        total_receitas = LancamentoFinanceiro.objects.filter(tipo="R").aggregate(
            total=django.db.models.Sum('valor')
        )['total']
        
        self.assertEqual(total_receitas, Decimal("3500.00"))
        
        logger.info("Teste de criação de lançamentos de receitas concluído com sucesso")
        return [receita1, receita2]
    
    def test_2_criar_lancamentos_despesas(self):
        """Teste de criação de lançamentos de despesas."""
        logger.info("Testando criação de lançamentos de despesas")
        
        # Criar lançamentos de despesas
        despesa1 = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=Decimal("500.00"),
            descricao="Compra de suprimentos do Fornecedor A",
            tipo="D",  # Despesa
            categoria=self.cat_fornecedores,
            conta=self.conta_principal,
            fornecedor=self.fornecedor1,
            status="PG"  # Pago
        )
        
        despesa2 = LancamentoFinanceiro.objects.create(
            data=timezone.now().date() + datetime.timedelta(days=1),
            valor=Decimal("1200.00"),
            descricao="Pagamento de imposto municipal",
            tipo="D",  # Despesa
            categoria=self.cat_impostos,
            conta=self.conta_principal,
            status="PG"  # Pago
        )
        
        despesa3 = LancamentoFinanceiro.objects.create(
            data=timezone.now().date() + datetime.timedelta(days=2),
            valor=Decimal("3000.00"),
            descricao="Pagamento de salários",
            tipo="D",  # Despesa
            categoria=self.cat_folha,
            conta=self.conta_principal,
            status="PG"  # Pago
        )
        
        # Verificações
        self.assertEqual(LancamentoFinanceiro.objects.filter(tipo="D").count(), 3)
        self.assertEqual(LancamentoFinanceiro.objects.filter(categoria=self.cat_fornecedores).count(), 1)
        self.assertEqual(LancamentoFinanceiro.objects.filter(categoria=self.cat_impostos).count(), 1)
        self.assertEqual(LancamentoFinanceiro.objects.filter(categoria=self.cat_folha).count(), 1)
        
        # Verificar valor total de despesas
        total_despesas = LancamentoFinanceiro.objects.filter(tipo="D").aggregate(
            total=django.db.models.Sum('valor')
        )['total']
        
        self.assertEqual(total_despesas, Decimal("4700.00"))
        
        logger.info("Teste de criação de lançamentos de despesas concluído com sucesso")
        return [despesa1, despesa2, despesa3]
    
    def test_3_lancamentos_pendentes(self):
        """Teste de lançamentos pendentes."""
        logger.info("Testando lançamentos pendentes")
        
        # Criar lançamentos pendentes
        receita_pendente = LancamentoFinanceiro.objects.create(
            data=timezone.now().date() + datetime.timedelta(days=5),
            valor=Decimal("3000.00"),
            descricao="Serviço futuro para Cliente X",
            tipo="R",  # Receita
            categoria=self.cat_servicos,
            conta=self.conta_principal,
            cliente=self.cliente1,
            status="PD"  # Pendente
        )
        
        despesa_pendente = LancamentoFinanceiro.objects.create(
            data=timezone.now().date() + datetime.timedelta(days=7),
            valor=Decimal("800.00"),
            descricao="Compra futura do Fornecedor B",
            tipo="D",  # Despesa
            categoria=self.cat_fornecedores,
            conta=self.conta_principal,
            fornecedor=self.fornecedor2,
            status="PD"  # Pendente
        )
        
        # Verificações
        self.assertEqual(LancamentoFinanceiro.objects.filter(status="PD").count(), 2)
        
        # Verificar valor total pendente
        total_pendente_receitas = LancamentoFinanceiro.objects.filter(
            tipo="R", status="PD"
        ).aggregate(total=django.db.models.Sum('valor'))['total']
        
        total_pendente_despesas = LancamentoFinanceiro.objects.filter(
            tipo="D", status="PD"
        ).aggregate(total=django.db.models.Sum('valor'))['total']
        
        self.assertEqual(total_pendente_receitas, Decimal("3000.00"))
        self.assertEqual(total_pendente_despesas, Decimal("800.00"))
        
        logger.info("Teste de lançamentos pendentes concluído com sucesso")
        return [receita_pendente, despesa_pendente]
    
    def test_4_atualizar_lancamento(self):
        """Teste de atualização de lançamento."""
        logger.info("Testando atualização de lançamento")
        
        # Criar lançamento para teste
        lancamento = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=Decimal("1000.00"),
            descricao="Lançamento para teste de atualização",
            tipo="D",  # Despesa
            categoria=self.cat_fornecedores,
            conta=self.conta_principal,
            fornecedor=self.fornecedor1,
            status="PD"  # Pendente
        )
        
        # Atualizar lançamento
        lancamento.valor = Decimal("1200.00")
        lancamento.descricao = "Lançamento atualizado"
        lancamento.status = "PG"  # Alterar para pago
        lancamento.save()
        
        # Verificar atualização
        lancamento_atualizado = LancamentoFinanceiro.objects.get(pk=lancamento.pk)
        self.assertEqual(lancamento_atualizado.valor, Decimal("1200.00"))
        self.assertEqual(lancamento_atualizado.descricao, "Lançamento atualizado")
        self.assertEqual(lancamento_atualizado.status, "PG")
        
        logger.info("Teste de atualização de lançamento concluído com sucesso")
    
    def test_5_excluir_lancamento(self):
        """Teste de exclusão de lançamento."""
        logger.info("Testando exclusão de lançamento")
        
        # Criar lançamento para teste
        lancamento = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=Decimal("500.00"),
            descricao="Lançamento para teste de exclusão",
            tipo="D",  # Despesa
            categoria=self.cat_fornecedores,
            conta=self.conta_principal,
            fornecedor=self.fornecedor1,
            status="PG"  # Pago
        )
        
        # Guardar contagem inicial
        count_inicial = LancamentoFinanceiro.objects.count()
        
        # Excluir lançamento
        lancamento.delete()
        
        # Verificar exclusão
        self.assertEqual(LancamentoFinanceiro.objects.count(), count_inicial - 1)
        with self.assertRaises(LancamentoFinanceiro.DoesNotExist):
            LancamentoFinanceiro.objects.get(pk=lancamento.pk)
        
        logger.info("Teste de exclusão de lançamento concluído com sucesso")
    
    def test_6_gerar_fluxo_caixa(self):
        """Teste de geração de fluxo de caixa."""
        logger.info("Testando geração de fluxo de caixa")
        
        # Criar lançamentos para o teste
        self.test_1_criar_lancamentos_receitas()
        self.test_2_criar_lancamentos_despesas()
        self.test_3_lancamentos_pendentes()
        
        # Definir período para o fluxo de caixa
        data_inicial = timezone.now().date()
        data_final = data_inicial + datetime.timedelta(days=10)
        
        # Gerar fluxo de caixa (simulação)
        def gerar_fluxo_caixa(data_inicial, data_final):
            fluxo = {
                "periodo": {
                    "inicio": data_inicial.strftime("%d/%m/%Y"),
                    "fim": data_final.strftime("%d/%m/%Y")
                },
                "saldo_inicial": float(self.conta_principal.saldo_inicial),
                "receitas": {
                    "total": 0,
                    "categorias": {}
                },
                "despesas": {
                    "total": 0,
                    "categorias": {}
                },
                "saldo_final": float(self.conta_principal.saldo_inicial)
            }
            
            # Calcular receitas por categoria
            receitas = LancamentoFinanceiro.objects.filter(
                tipo="R",
                status="PG",
                data__gte=data_inicial,
                data__lte=data_final
            )
            
            for receita in receitas:
                categoria = receita.categoria.nome
                valor = float(receita.valor)
                
                if categoria not in fluxo["receitas"]["categorias"]:
                    fluxo["receitas"]["categorias"][categoria] = 0
                
                fluxo["receitas"]["categorias"][categoria] += valor
                fluxo["receitas"]["total"] += valor
                fluxo["saldo_final"] += valor
            
            # Calcular despesas por categoria
            despesas = LancamentoFinanceiro.objects.filter(
                tipo="D",
                status="PG",
                data__gte=data_inicial,
                data__lte=data_final
            )
            
            for despesa in despesas:
                categoria = despesa.categoria.nome
                valor = float(despesa.valor)
                
                if categoria not in fluxo["despesas"]["categorias"]:
                    fluxo["despesas"]["categorias"][categoria] = 0
                
                fluxo["despesas"]["categorias"][categoria] += valor
                fluxo["despesas"]["total"] += valor
                fluxo["saldo_final"] -= valor
            
            return fluxo
        
        # Gerar fluxo de caixa
        fluxo = gerar_fluxo_caixa(data_inicial, data_final)
        
        # Verificações
        self.assertEqual(fluxo["receitas"]["total"], 3500.0)  # 1500 + 2000
        self.assertEqual(fluxo["despesas"]["total"], 4700.0)  # 500 + 1200 + 3000
        self.assertEqual(fluxo["saldo_final"], 8800.0)  # 10000 + 3500 - 4700
        
        logger.info("Teste de geração de fluxo de caixa concluído com sucesso")
        return fluxo
    
    def test_7_gerar_dre(self):
        """Teste de geração de DRE (Demonstração do Resultado do Exercício)."""
        logger.info("Testando geração de DRE")
        
        # Criar lançamentos para o teste
        self.test_1_criar_lancamentos_receitas()
        self.test_2_criar_lancamentos_despesas()
        
        # Definir período para o DRE
        data_inicial = timezone.now().date()
        data_final = data_inicial + datetime.timedelta(days=10)
        
        # Gerar DRE (simulação)
        def gerar_dre(data_inicial, data_final):
            dre = {
                "periodo": {
                    "inicio": data_inicial.strftime("%d/%m/%Y"),
                    "fim": data_final.strftime("%d/%m/%Y")
                },
                "receita_bruta": 0,
                "impostos": 0,
                "receita_liquida": 0,
                "custos": 0,
                "lucro_bruto": 0,
                "despesas_operacionais": 0,
                "resultado_operacional": 0,
                "resultado_final": 0
            }
            
            # Calcular receita bruta
            receitas = LancamentoFinanceiro.objects.filter(
                tipo="R",
                data__gte=data_inicial,
                data__lte=data_final
            )
            
            for receita in receitas:
                dre["receita_bruta"] += float(receita.valor)
            
            # Calcular impostos (simulação)
            dre["impostos"] = LancamentoFinanceiro.objects.filter(
                tipo="D",
                categoria=self.cat_impostos,
                data__gte=data_inicial,
                data__lte=data_final
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            dre["impostos"] = float(dre["impostos"])
            
            # Calcular receita líquida
            dre["receita_liquida"] = dre["receita_bruta"] - dre["impostos"]
            
            # Calcular custos (fornecedores)
            dre["custos"] = LancamentoFinanceiro.objects.filter(
                tipo="D",
                categoria=self.cat_fornecedores,
                data__gte=data_inicial,
                data__lte=data_final
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            dre["custos"] = float(dre["custos"])
            
            # Calcular lucro bruto
            dre["lucro_bruto"] = dre["receita_liquida"] - dre["custos"]
            
            # Calcular despesas operacionais (folha de pagamento)
            dre["despesas_operacionais"] = LancamentoFinanceiro.objects.filter(
                tipo="D",
                categoria=self.cat_folha,
                data__gte=data_inicial,
                data__lte=data_final
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            dre["despesas_operacionais"] = float(dre["despesas_operacionais"])
            
            # Calcular resultado operacional
            dre["resultado_operacional"] = dre["lucro_bruto"] - dre["despesas_operacionais"]
            
            # Resultado final (sem outras receitas/despesas)
            dre["resultado_final"] = dre["resultado_operacional"]
            
            return dre
        
        # Gerar DRE
        dre = gerar_dre(data_inicial, data_final)
        
        # Verificações
        self.assertEqual(dre["receita_bruta"], 3500.0)  # 1500 + 2000
        self.assertEqual(dre["impostos"], 1200.0)
        self.assertEqual(dre["receita_liquida"], 2300.0)  # 3500 - 1200
        self.assertEqual(dre["custos"], 500.0)
        self.assertEqual(dre["lucro_bruto"], 1800.0)  # 2300 - 500
        self.assertEqual(dre["despesas_operacionais"], 3000.0)
        self.assertEqual(dre["resultado_operacional"], -1200.0)  # 1800 - 3000
        self.assertEqual(dre["resultado_final"], -1200.0)
        
        logger.info("Teste de geração de DRE concluído com sucesso")
        return dre
    
    def test_8_saldo_contas(self):
        """Teste de cálculo do saldo das contas."""
        logger.info("Testando cálculo do saldo das contas")
        
        # Criar lançamentos para o teste
        self.test_1_criar_lancamentos_receitas()
        self.test_2_criar_lancamentos_despesas()
        
        # Função para calcular saldo da conta
        def calcular_saldo_conta(conta):
            saldo = conta.saldo_inicial
            
            # Somar receitas
            receitas = LancamentoFinanceiro.objects.filter(
                conta=conta,
                tipo="R",
                status="PG"
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            # Subtrair despesas
            despesas = LancamentoFinanceiro.objects.filter(
                conta=conta,
                tipo="D",
                status="PG"
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            saldo += receitas - despesas
            return saldo
        
        # Calcular saldo da conta principal
        saldo_calculado = calcular_saldo_conta(self.conta_principal)
        
        # Verificar saldo
        self.assertEqual(saldo_calculado, Decimal("8800.00"))  # 10000 + 3500 - 4700
        
        logger.info("Teste de cálculo de saldo das contas concluído com sucesso")
    
    def test_9_transferencia_entre_contas(self):
        """Teste de transferência entre contas."""
        logger.info("Testando transferência entre contas")
        
        # Registrar transferência
        valor_transferencia = Decimal("2000.00")
        
        # Lançamento de saída (conta principal)
        saida = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=valor_transferencia,
            descricao="Transferência para Conta Investimentos",
            tipo="D",  # Despesa na conta de origem
            categoria=self.cat_despesas.categorias.first(),  # Usar primeira categoria disponível
            conta=self.conta_principal,
            status="PG",  # Pago
            is_transferencia=True,
            conta_destino=self.conta_investimentos
        )
        
        # Lançamento de entrada (conta investimentos)
        entrada = LancamentoFinanceiro.objects.create(
            data=timezone.now().date(),
            valor=valor_transferencia,
            descricao="Transferência da Conta Principal",
            tipo="R",  # Receita na conta de destino
            categoria=self.cat_receitas.categorias.first(),  # Usar primeira categoria disponível
            conta=self.conta_investimentos,
            status="PG",  # Pago
            is_transferencia=True,
            conta_origem=self.conta_principal
        )
        
        # Função para calcular saldo da conta
        def calcular_saldo_conta(conta):
            saldo = conta.saldo_inicial
            
            # Somar receitas
            receitas = LancamentoFinanceiro.objects.filter(
                conta=conta,
                tipo="R",
                status="PG"
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            # Subtrair despesas
            despesas = LancamentoFinanceiro.objects.filter(
                conta=conta,
                tipo="D",
                status="PG"
            ).aggregate(total=django.db.models.Sum('valor'))['total'] or 0
            
            saldo += receitas - despesas
            return saldo
        
        # Calcular novos saldos
        saldo_principal = calcular_saldo_conta(self.conta_principal)
        saldo_investimentos = calcular_saldo_conta(self.conta_investimentos)
        
        # Verificar saldos
        self.assertEqual(saldo_principal, self.conta_principal.saldo_inicial - valor_transferencia)
        self.assertEqual(saldo_investimentos, self.conta_investimentos.saldo_inicial + valor_transferencia)
        
        logger.info("Teste de transferência entre contas concluído com sucesso")

def run_tests():
    """Executa todos os testes."""
    # Criar suite de testes
    suite = unittest.TestSuite()
    suite.addTest(FinanceiroTestCase('test_1_criar_lancamentos_receitas'))
    suite.addTest(FinanceiroTestCase('test_2_criar_lancamentos_despesas'))
    suite.addTest(FinanceiroTestCase('test_3_lancamentos_pendentes'))
    suite.addTest(FinanceiroTestCase('test_4_atualizar_lancamento'))
    suite.addTest(FinanceiroTestCase('test_5_excluir_lancamento'))
    suite.addTest(FinanceiroTestCase('test_6_gerar_fluxo_caixa'))
    suite.addTest(FinanceiroTestCase('test_7_gerar_dre'))
    suite.addTest(FinanceiroTestCase('test_8_saldo_contas'))
    suite.addTest(FinanceiroTestCase('test_9_transferencia_entre_contas'))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar código de saída apropriado
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    # Executar os testes dentro de uma transação para não modificar o banco de dados
    with transaction.atomic():
        sys.exit(run_tests()) 