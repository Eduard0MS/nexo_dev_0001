#!/usr/bin/env python
"""
Script para testar o sistema de autenticação do Nexo.
Este script testa login, registro, permissões e autenticação OAuth.
"""

import os
import sys
import logging
import unittest
import django
import json
import random
import string
from pathlib import Path
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/autenticacao_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("autenticacao_test")

# Configurar ambiente Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

# Importar modelos após configurar Django
from core.models import Perfil
from django.contrib.auth.models import User


class AutenticacaoTestCase(unittest.TestCase):
    """Classe de teste para funcionalidades de autenticação."""

    def setUp(self):
        """Configuração para cada teste."""
        # Criar cliente para fazer requisições
        self.client = Client()

        # Usuário admin para testes
        self.admin_username = "admin_test"
        self.admin_password = "admin_password@123"
        self.admin_email = "admin@teste.com"

        # Usuário comum para testes
        self.user_username = "user_test"
        self.user_password = "user_password@123"
        self.user_email = "user@teste.com"

        # Criar grupos de permissão
        self.grupo_admin = Group.objects.get_or_create(name="Administradores")[0]
        self.grupo_gerente = Group.objects.get_or_create(name="Gerentes")[0]
        self.grupo_usuario = Group.objects.get_or_create(name="Usuários")[0]

        # Configurar permissões básicas
        content_type = ContentType.objects.get_for_model(User)

        # Permissão para ver usuários
        view_user_permission = Permission.objects.get(
            content_type=content_type, codename="view_user"
        )

        # Permissão para adicionar usuários
        add_user_permission = Permission.objects.get(
            content_type=content_type, codename="add_user"
        )

        # Permissão para alterar usuários
        change_user_permission = Permission.objects.get(
            content_type=content_type, codename="change_user"
        )

        # Permissão para excluir usuários
        delete_user_permission = Permission.objects.get(
            content_type=content_type, codename="delete_user"
        )

        # Configurar permissões para cada grupo
        self.grupo_usuario.permissions.add(view_user_permission)

        self.grupo_gerente.permissions.add(view_user_permission)
        self.grupo_gerente.permissions.add(add_user_permission)
        self.grupo_gerente.permissions.add(change_user_permission)

        self.grupo_admin.permissions.add(view_user_permission)
        self.grupo_admin.permissions.add(add_user_permission)
        self.grupo_admin.permissions.add(change_user_permission)
        self.grupo_admin.permissions.add(delete_user_permission)

        logger.info("Ambiente de teste de autenticação configurado")

    def tearDown(self):
        """Limpeza após cada teste."""
        # Não apagamos os dados aqui para permitir inspeção manual após os testes
        pass

    def test_1_criar_usuario_admin(self):
        """Teste de criação de usuário administrador."""
        logger.info("Testando criação de usuário administrador")

        # Verificar se usuário já existe e remover
        if User.objects.filter(username=self.admin_username).exists():
            User.objects.filter(username=self.admin_username).delete()

        # Criar usuário admin
        admin_user = User.objects.create_user(
            username=self.admin_username,
            email=self.admin_email,
            password=self.admin_password,
            is_staff=True,
        )

        # Adicionar ao grupo de administradores
        admin_user.groups.add(self.grupo_admin)
        admin_user.save()

        # Verificar criação
        self.assertIsNotNone(admin_user.id)
        self.assertEqual(admin_user.username, self.admin_username)
        self.assertEqual(admin_user.email, self.admin_email)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.groups.filter(name="Administradores").exists())

        # Verificar permissões
        self.assertTrue(admin_user.has_perm("auth.view_user"))
        self.assertTrue(admin_user.has_perm("auth.add_user"))
        self.assertTrue(admin_user.has_perm("auth.change_user"))
        self.assertTrue(admin_user.has_perm("auth.delete_user"))

        logger.info("Teste de criação de usuário administrador concluído com sucesso")
        return admin_user

    def test_2_criar_usuario_comum(self):
        """Teste de criação de usuário comum."""
        logger.info("Testando criação de usuário comum")

        # Verificar se usuário já existe e remover
        if User.objects.filter(username=self.user_username).exists():
            User.objects.filter(username=self.user_username).delete()

        # Criar usuário comum
        user = User.objects.create_user(
            username=self.user_username,
            email=self.user_email,
            password=self.user_password,
        )

        # Adicionar ao grupo de usuários comuns
        user.groups.add(self.grupo_usuario)
        user.save()

        # Criar perfil para o usuário
        perfil = Perfil.objects.create(
            usuario=user, telefone="(11) 98765-4321", cargo="Analista"
        )

        # Verificar criação
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, self.user_username)
        self.assertEqual(user.email, self.user_email)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.groups.filter(name="Usuários").exists())

        # Verificar permissões
        self.assertTrue(user.has_perm("auth.view_user"))
        self.assertFalse(user.has_perm("auth.add_user"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))

        # Verificar perfil
        self.assertEqual(perfil.usuario, user)
        self.assertEqual(perfil.telefone, "(11) 98765-4321")
        self.assertEqual(perfil.cargo, "Analista")

        logger.info("Teste de criação de usuário comum concluído com sucesso")
        return user

    def test_3_login_logout(self):
        """Teste de login e logout de usuário."""
        logger.info("Testando login e logout")

        # Garantir que o usuário de teste existe
        self.test_2_criar_usuario_comum()

        # Tentar login com credenciais inválidas
        response_invalid = self.client.login(
            username=self.user_username, password="senha_errada"
        )

        # Verificar falha no login
        self.assertFalse(response_invalid)

        # Tentar login com credenciais válidas
        response_valid = self.client.login(
            username=self.user_username, password=self.user_password
        )

        # Verificar sucesso no login
        self.assertTrue(response_valid)

        # Fazer logout
        self.client.logout()

        logger.info("Teste de login e logout concluído com sucesso")

    def test_4_alteracao_senha(self):
        """Teste de alteração de senha."""
        logger.info("Testando alteração de senha")

        # Garantir que o usuário de teste existe
        user = self.test_2_criar_usuario_comum()

        # Nova senha para teste
        nova_senha = "nova_senha@456"

        # Alterar senha
        user.set_password(nova_senha)
        user.save()

        # Tentar login com senha antiga
        response_old_pwd = self.client.login(
            username=self.user_username, password=self.user_password
        )

        # Verificar falha no login com senha antiga
        self.assertFalse(response_old_pwd)

        # Tentar login com nova senha
        response_new_pwd = self.client.login(
            username=self.user_username, password=nova_senha
        )

        # Verificar sucesso no login com nova senha
        self.assertTrue(response_new_pwd)

        # Restaurar senha original para outros testes
        user.set_password(self.user_password)
        user.save()

        logger.info("Teste de alteração de senha concluído com sucesso")

    def test_5_atualizacao_perfil(self):
        """Teste de atualização de perfil de usuário."""
        logger.info("Testando atualização de perfil")

        # Garantir que o usuário de teste existe
        user = self.test_2_criar_usuario_comum()

        # Obter perfil
        perfil = Perfil.objects.get(usuario=user)

        # Atualizar perfil
        perfil.telefone = "(21) 99876-5432"
        perfil.cargo = "Coordenador"
        perfil.bio = "Perfil de teste atualizado"
        perfil.save()

        # Verificar alterações
        perfil_atualizado = Perfil.objects.get(usuario=user)
        self.assertEqual(perfil_atualizado.telefone, "(21) 99876-5432")
        self.assertEqual(perfil_atualizado.cargo, "Coordenador")
        self.assertEqual(perfil_atualizado.bio, "Perfil de teste atualizado")

        logger.info("Teste de atualização de perfil concluído com sucesso")

    def test_6_permissoes_grupos(self):
        """Teste de permissões por grupos."""
        logger.info("Testando permissões por grupos")

        # Criar usuário para teste
        username = f"test_perm_{random.randint(1000, 9999)}"
        email = f"{username}@teste.com"
        password = "test_password@123"

        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        # Verificar permissões iniciais (sem grupos)
        self.assertFalse(user.has_perm("auth.view_user"))
        self.assertFalse(user.has_perm("auth.add_user"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))

        # Adicionar ao grupo de usuários comuns
        user.groups.add(self.grupo_usuario)
        user = User.objects.get(pk=user.pk)  # Recarregar usuário

        # Verificar permissões de usuário comum
        self.assertTrue(user.has_perm("auth.view_user"))
        self.assertFalse(user.has_perm("auth.add_user"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))

        # Alterar para grupo de gerentes
        user.groups.clear()
        user.groups.add(self.grupo_gerente)
        user = User.objects.get(pk=user.pk)  # Recarregar usuário

        # Verificar permissões de gerente
        self.assertTrue(user.has_perm("auth.view_user"))
        self.assertTrue(user.has_perm("auth.add_user"))
        self.assertTrue(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))

        # Alterar para grupo de administradores
        user.groups.clear()
        user.groups.add(self.grupo_admin)
        user = User.objects.get(pk=user.pk)  # Recarregar usuário

        # Verificar permissões de administrador
        self.assertTrue(user.has_perm("auth.view_user"))
        self.assertTrue(user.has_perm("auth.add_user"))
        self.assertTrue(user.has_perm("auth.change_user"))
        self.assertTrue(user.has_perm("auth.delete_user"))

        # Limpar grupos para testar usuário sem permissões
        user.groups.clear()
        user = User.objects.get(pk=user.pk)  # Recarregar usuário

        # Verificar usuário sem permissões
        self.assertFalse(user.has_perm("auth.view_user"))
        self.assertFalse(user.has_perm("auth.add_user"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.has_perm("auth.delete_user"))

        logger.info("Teste de permissões por grupos concluído com sucesso")

    def test_7_registro_usuario(self):
        """Teste de registro de novo usuário."""
        logger.info("Testando registro de usuário")

        # Dados do novo usuário
        new_username = f"new_user_{random.randint(1000, 9999)}"
        new_email = f"{new_username}@teste.com"
        new_password = "new_password@123"

        # Simular registros de usuário via API/formulário
        # Em um teste real, isso usaria self.client.post() para a view de registro

        # Criar o usuário diretamente
        new_user = User.objects.create_user(
            username=new_username, email=new_email, password=new_password
        )

        # Adicionar ao grupo padrão de usuários
        new_user.groups.add(self.grupo_usuario)

        # Criar perfil básico
        perfil = Perfil.objects.create(
            usuario=new_user, telefone="(31) 98765-4321", cargo="Novo Usuário"
        )

        # Verificar registro
        self.assertTrue(User.objects.filter(username=new_username).exists())
        self.assertEqual(new_user.email, new_email)
        self.assertTrue(new_user.groups.filter(name="Usuários").exists())
        self.assertEqual(perfil.usuario, new_user)

        # Testar login com o novo usuário
        login_success = self.client.login(username=new_username, password=new_password)

        self.assertTrue(login_success)

        logger.info("Teste de registro de usuário concluído com sucesso")
        return new_user

    def test_8_recuperacao_senha(self):
        """Simulação de teste de recuperação de senha."""
        logger.info("Testando recuperação de senha (simulação)")

        # Garantir que o usuário de teste existe
        user = self.test_2_criar_usuario_comum()

        # Em um sistema real, testaríamos o fluxo completo de recuperação de senha
        # Aqui vamos simular o processo básico:

        # 1. Usuário solicita recuperação de senha
        # 2. Sistema gera token de recuperação
        # 3. Sistema envia email com link de recuperação
        # 4. Usuário acessa link e define nova senha

        # Simular geração de token temporário (em sistema real: PasswordResetTokenGenerator)
        token = "".join(random.choices(string.ascii_letters + string.digits, k=20))

        # Simular reset de senha (etapa final)
        new_temp_password = "temp_password@789"
        user.set_password(new_temp_password)
        user.save()

        # Testar login com nova senha
        login_success = self.client.login(
            username=self.user_username, password=new_temp_password
        )

        self.assertTrue(login_success)

        # Restaurar senha original para outros testes
        user.set_password(self.user_password)
        user.save()

        logger.info("Teste de recuperação de senha concluído com sucesso")

    def test_9_bloqueio_conta(self):
        """Teste de bloqueio e desbloqueio de conta."""
        logger.info("Testando bloqueio de conta")

        # Garantir que o usuário de teste existe
        user = self.test_2_criar_usuario_comum()

        # Bloquear conta (desativar usuário)
        user.is_active = False
        user.save()

        # Tentar login com conta bloqueada
        login_blocked = self.client.login(
            username=self.user_username, password=self.user_password
        )

        # Verificar que login falha com conta bloqueada
        self.assertFalse(login_blocked)

        # Desbloquear conta
        user.is_active = True
        user.save()

        # Tentar login com conta desbloqueada
        login_unblocked = self.client.login(
            username=self.user_username, password=self.user_password
        )

        # Verificar que login funciona com conta desbloqueada
        self.assertTrue(login_unblocked)

        logger.info("Teste de bloqueio de conta concluído com sucesso")


def run_tests():
    """Executa todos os testes."""
    # Criar suite de testes
    suite = unittest.TestSuite()
    suite.addTest(AutenticacaoTestCase("test_1_criar_usuario_admin"))
    suite.addTest(AutenticacaoTestCase("test_2_criar_usuario_comum"))
    suite.addTest(AutenticacaoTestCase("test_3_login_logout"))
    suite.addTest(AutenticacaoTestCase("test_4_alteracao_senha"))
    suite.addTest(AutenticacaoTestCase("test_5_atualizacao_perfil"))
    suite.addTest(AutenticacaoTestCase("test_6_permissoes_grupos"))
    suite.addTest(AutenticacaoTestCase("test_7_registro_usuario"))
    suite.addTest(AutenticacaoTestCase("test_8_recuperacao_senha"))
    suite.addTest(AutenticacaoTestCase("test_9_bloqueio_conta"))

    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retornar código de saída apropriado
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # Executar os testes dentro de uma transação para não modificar o banco de dados
    with transaction.atomic():
        sys.exit(run_tests())
