#!/usr/bin/env python
"""
Script para testar a funcionalidade do organograma do Nexo.
Este script testa operações CRUD para departamentos e funcionários,
bem como as relações hierárquicas entre eles.
"""

import os
import sys
import logging
import json
import random
import string
import requests
from pathlib import Path
import unittest
import django
from django.db import transaction

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/organograma_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("organograma_test")

# Configurar ambiente Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

# Importar modelos após configurar Django
from core.models import Departamento, Funcionario, Cargo


class OrganogramaTestCase(unittest.TestCase):
    """Classe de teste para funcionalidades do organograma."""

    def setUp(self):
        """Configuração para cada teste."""
        # Limpar dados existentes
        Funcionario.objects.all().delete()
        Departamento.objects.all().delete()
        Cargo.objects.all().delete()

        # Criar cargos básicos para teste
        self.cargos = [
            Cargo.objects.create(nome="Diretor", nivel=1),
            Cargo.objects.create(nome="Gerente", nivel=2),
            Cargo.objects.create(nome="Supervisor", nivel=3),
            Cargo.objects.create(nome="Analista", nivel=4),
            Cargo.objects.create(nome="Assistente", nivel=5),
        ]

        logger.info("Ambiente de teste configurado")

    def tearDown(self):
        """Limpeza após cada teste."""
        # Não apagamos os dados aqui para permitir inspeção manual após os testes
        pass

    def test_1_criar_departamentos(self):
        """Teste de criação de departamentos."""
        logger.info("Testando criação de departamentos")

        # Criar departamentos
        departamentos = [
            Departamento.objects.create(
                nome="Diretoria", descricao="Diretoria executiva"
            ),
            Departamento.objects.create(
                nome="Recursos Humanos", descricao="Gestão de pessoal"
            ),
            Departamento.objects.create(
                nome="Financeiro", descricao="Gestão financeira"
            ),
            Departamento.objects.create(
                nome="TI", descricao="Tecnologia da Informação"
            ),
            Departamento.objects.create(
                nome="Marketing", descricao="Marketing e comunicação"
            ),
        ]

        # Configurar hierarquia
        departamentos[1].departamento_pai = departamentos[
            0
        ]  # RH subordinado à Diretoria
        departamentos[1].save()

        departamentos[2].departamento_pai = departamentos[
            0
        ]  # Financeiro subordinado à Diretoria
        departamentos[2].save()

        departamentos[3].departamento_pai = departamentos[
            0
        ]  # TI subordinado à Diretoria
        departamentos[3].save()

        departamentos[4].departamento_pai = departamentos[
            0
        ]  # Marketing subordinado à Diretoria
        departamentos[4].save()

        # Verificações
        self.assertEqual(Departamento.objects.count(), 5)
        self.assertEqual(departamentos[0].departamentos_filhos.count(), 4)

        # Verificar hierarquia
        for i in range(1, 5):
            self.assertEqual(departamentos[i].departamento_pai, departamentos[0])

        logger.info("Teste de criação de departamentos concluído com sucesso")

    def test_2_criar_funcionarios(self):
        """Teste de criação de funcionários."""
        logger.info("Testando criação de funcionários")

        # Primeiro, garantir que temos departamentos
        self.test_1_criar_departamentos()
        departamentos = list(Departamento.objects.all())

        # Criar funcionários
        diretor = Funcionario.objects.create(
            nome="João Silva",
            email="joao.silva@exemplo.com",
            telefone="(11) 98765-4321",
            data_nascimento="1975-05-15",
            data_contratacao="2010-01-10",
            departamento=departamentos[0],  # Diretoria
            cargo=self.cargos[0],  # Diretor
        )

        gerente_rh = Funcionario.objects.create(
            nome="Maria Oliveira",
            email="maria.oliveira@exemplo.com",
            telefone="(11) 98765-4322",
            data_nascimento="1980-07-20",
            data_contratacao="2012-03-15",
            departamento=departamentos[1],  # RH
            cargo=self.cargos[1],  # Gerente
            supervisor=diretor,
        )

        gerente_ti = Funcionario.objects.create(
            nome="Pedro Santos",
            email="pedro.santos@exemplo.com",
            telefone="(11) 98765-4323",
            data_nascimento="1982-10-05",
            data_contratacao="2013-06-20",
            departamento=departamentos[3],  # TI
            cargo=self.cargos[1],  # Gerente
            supervisor=diretor,
        )

        analista_ti = Funcionario.objects.create(
            nome="Ana Costa",
            email="ana.costa@exemplo.com",
            telefone="(11) 98765-4324",
            data_nascimento="1990-12-15",
            data_contratacao="2018-02-10",
            departamento=departamentos[3],  # TI
            cargo=self.cargos[3],  # Analista
            supervisor=gerente_ti,
        )

        # Verificações
        self.assertEqual(Funcionario.objects.count(), 4)
        self.assertEqual(diretor.subordinados.count(), 2)
        self.assertEqual(gerente_ti.subordinados.count(), 1)
        self.assertEqual(analista_ti.supervisor, gerente_ti)
        self.assertEqual(gerente_ti.supervisor, diretor)

        logger.info("Teste de criação de funcionários concluído com sucesso")

    def test_3_editar_departamento(self):
        """Teste de edição de departamento."""
        logger.info("Testando edição de departamento")

        # Primeiro, garantir que temos departamentos
        self.test_1_criar_departamentos()

        # Editar um departamento
        departamento = Departamento.objects.get(nome="TI")
        departamento.nome = "Tecnologia da Informação"
        departamento.descricao = "Suporte técnico e desenvolvimento de sistemas"
        departamento.save()

        # Verificar alterações
        departamento_atualizado = Departamento.objects.get(pk=departamento.pk)
        self.assertEqual(departamento_atualizado.nome, "Tecnologia da Informação")
        self.assertEqual(
            departamento_atualizado.descricao,
            "Suporte técnico e desenvolvimento de sistemas",
        )

        logger.info("Teste de edição de departamento concluído com sucesso")

    def test_4_editar_funcionario(self):
        """Teste de edição de funcionário."""
        logger.info("Testando edição de funcionário")

        # Primeiro, garantir que temos funcionários
        self.test_2_criar_funcionarios()

        # Editar um funcionário
        funcionario = Funcionario.objects.get(nome="Ana Costa")
        funcionario.nome = "Ana Paula Costa"
        funcionario.email = "anapaula.costa@exemplo.com"
        funcionario.telefone = "(11) 98765-9876"
        funcionario.cargo = self.cargos[2]  # Promover para Supervisor
        funcionario.save()

        # Verificar alterações
        funcionario_atualizado = Funcionario.objects.get(pk=funcionario.pk)
        self.assertEqual(funcionario_atualizado.nome, "Ana Paula Costa")
        self.assertEqual(funcionario_atualizado.email, "anapaula.costa@exemplo.com")
        self.assertEqual(funcionario_atualizado.telefone, "(11) 98765-9876")
        self.assertEqual(funcionario_atualizado.cargo.nome, "Supervisor")

        logger.info("Teste de edição de funcionário concluído com sucesso")

    def test_5_excluir_funcionario(self):
        """Teste de exclusão de funcionário."""
        logger.info("Testando exclusão de funcionário")

        # Primeiro, garantir que temos funcionários
        self.test_2_criar_funcionarios()

        # Guardar contagem inicial
        count_inicial = Funcionario.objects.count()

        # Excluir um funcionário
        funcionario = Funcionario.objects.get(nome="Ana Costa")
        funcionario.delete()

        # Verificar exclusão
        self.assertEqual(Funcionario.objects.count(), count_inicial - 1)
        with self.assertRaises(Funcionario.DoesNotExist):
            Funcionario.objects.get(nome="Ana Costa")

        logger.info("Teste de exclusão de funcionário concluído com sucesso")

    def test_6_excluir_departamento(self):
        """Teste de exclusão de departamento."""
        logger.info("Testando exclusão de departamento")

        # Primeiro, garantir que temos departamentos
        self.test_1_criar_departamentos()

        # Guardar contagem inicial
        count_inicial = Departamento.objects.count()

        # Remover funcionários do departamento para poder excluí-lo
        departamento = Departamento.objects.get(nome="Marketing")
        Funcionario.objects.filter(departamento=departamento).delete()

        # Excluir departamento
        departamento.delete()

        # Verificar exclusão
        self.assertEqual(Departamento.objects.count(), count_inicial - 1)
        with self.assertRaises(Departamento.DoesNotExist):
            Departamento.objects.get(nome="Marketing")

        logger.info("Teste de exclusão de departamento concluído com sucesso")

    def test_7_mover_funcionario(self):
        """Teste de movimentação de funcionário entre departamentos."""
        logger.info("Testando movimentação de funcionário entre departamentos")

        # Primeiro, garantir que temos funcionários e departamentos
        self.test_2_criar_funcionarios()

        # Mover funcionário para outro departamento
        funcionario = Funcionario.objects.get(nome="Ana Costa")
        departamento_destino = Departamento.objects.get(nome="Marketing")
        gerente_destino = Funcionario.objects.get(
            cargo__nome="Gerente", supervisor__isnull=False
        ).supervisor

        funcionario.departamento = departamento_destino
        funcionario.supervisor = gerente_destino
        funcionario.save()

        # Verificar alterações
        funcionario_atualizado = Funcionario.objects.get(pk=funcionario.pk)
        self.assertEqual(funcionario_atualizado.departamento.nome, "Marketing")
        self.assertEqual(funcionario_atualizado.supervisor, gerente_destino)

        logger.info("Teste de movimentação de funcionário concluído com sucesso")

    def test_8_criar_subdepartamento(self):
        """Teste de criação de subdepartamento."""
        logger.info("Testando criação de subdepartamento")

        # Primeiro, garantir que temos departamentos
        self.test_1_criar_departamentos()

        # Criar subdepartamento
        departamento_ti = Departamento.objects.get(nome="TI")
        subdepartamento = Departamento.objects.create(
            nome="Desenvolvimento",
            descricao="Equipe de desenvolvimento de software",
            departamento_pai=departamento_ti,
        )

        # Verificar hierarquia
        self.assertEqual(subdepartamento.departamento_pai, departamento_ti)
        self.assertIn(subdepartamento, departamento_ti.departamentos_filhos.all())

        logger.info("Teste de criação de subdepartamento concluído com sucesso")

    def test_9_gerar_organograma_completo(self):
        """Teste de geração do organograma completo."""
        logger.info("Testando geração do organograma completo")

        # Primeiro, garantir que temos funcionários e departamentos
        self.test_2_criar_funcionarios()
        self.test_8_criar_subdepartamento()

        # Função para gerar organograma (simulada aqui)
        def gerar_organograma():
            estrutura = {"nome": "Empresa", "departamentos": []}

            # Obter departamentos de nível superior
            for dept in Departamento.objects.filter(departamento_pai__isnull=True):
                dept_dict = {
                    "id": dept.id,
                    "nome": dept.nome,
                    "funcionarios": [],
                    "subdepartamentos": [],
                }

                # Adicionar funcionários do departamento
                for func in Funcionario.objects.filter(departamento=dept):
                    func_dict = {
                        "id": func.id,
                        "nome": func.nome,
                        "cargo": func.cargo.nome,
                    }
                    dept_dict["funcionarios"].append(func_dict)

                # Adicionar subdepartamentos
                for subdept in dept.departamentos_filhos.all():
                    subdept_dict = {
                        "id": subdept.id,
                        "nome": subdept.nome,
                        "funcionarios": [],
                    }

                    # Adicionar funcionários do subdepartamento
                    for func in Funcionario.objects.filter(departamento=subdept):
                        func_dict = {
                            "id": func.id,
                            "nome": func.nome,
                            "cargo": func.cargo.nome,
                        }
                        subdept_dict["funcionarios"].append(func_dict)

                    dept_dict["subdepartamentos"].append(subdept_dict)

                estrutura["departamentos"].append(dept_dict)

            return estrutura

        # Gerar organograma
        organograma = gerar_organograma()

        # Verificar estrutura básica
        self.assertIn("departamentos", organograma)
        self.assertTrue(len(organograma["departamentos"]) > 0)

        # Verificar departamento de nível superior (Diretoria)
        diretoria = None
        for dept in organograma["departamentos"]:
            if dept["nome"] == "Diretoria":
                diretoria = dept
                break

        self.assertIsNotNone(diretoria)
        self.assertTrue(len(diretoria["funcionarios"]) > 0)
        self.assertTrue(any(f["cargo"] == "Diretor" for f in diretoria["funcionarios"]))

        logger.info("Teste de geração do organograma concluído com sucesso")

        # Salvar organograma em arquivo para inspeção visual
        with open("organograma_teste.json", "w") as f:
            json.dump(organograma, f, indent=4)

        logger.info("Organograma salvo em organograma_teste.json")

        return organograma


def run_tests():
    """Executa todos os testes."""
    # Criar suite de testes
    suite = unittest.TestSuite()
    suite.addTest(OrganogramaTestCase("test_1_criar_departamentos"))
    suite.addTest(OrganogramaTestCase("test_2_criar_funcionarios"))
    suite.addTest(OrganogramaTestCase("test_3_editar_departamento"))
    suite.addTest(OrganogramaTestCase("test_4_editar_funcionario"))
    suite.addTest(OrganogramaTestCase("test_5_excluir_funcionario"))
    suite.addTest(OrganogramaTestCase("test_6_excluir_departamento"))
    suite.addTest(OrganogramaTestCase("test_7_mover_funcionario"))
    suite.addTest(OrganogramaTestCase("test_8_criar_subdepartamento"))
    suite.addTest(OrganogramaTestCase("test_9_gerar_organograma_completo"))

    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retornar código de saída apropriado
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # Executar os testes dentro de uma transação para não modificar o banco de dados
    with transaction.atomic():
        sys.exit(run_tests())
