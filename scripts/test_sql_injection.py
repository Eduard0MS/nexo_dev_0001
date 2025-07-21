#!/usr/bin/env python
"""Testes de segurança contra ataques de injeção SQL."""
import os
import sys
import logging
import unittest
from pathlib import Path

# Configurar ambiente Django para utilizar um banco SQLite
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
os.environ.setdefault("DATABASE_URL", "sqlite:///db.sqlite3")

import django

django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.db import connection
from django.db.utils import ProgrammingError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/sql_injection_test.log'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('sql_injection_test')


class SQLInjectionTestCase(unittest.TestCase):
    """Verifica proteções básicas contra injeção SQL."""

    def setUp(self):
        self.client = Client()
        self.username = 'inj_user'
        self.password = 'safe_password123'
        User.objects.filter(username=self.username).delete()
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_com_injecao(self):
        """Tentativa de login usando string maliciosa."""
        malicious = f"{self.username}' OR '1'='1"
        login = self.client.login(username=malicious, password='whatever')
        self.assertFalse(login)

    def test_injecao_em_consulta_raw(self):
        """Executa consulta raw malformada e verifica se a tabela permanece intacta."""
        payload = "'; DROP TABLE auth_user; --"
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT id FROM auth_user WHERE username = '{payload}'")
        except ProgrammingError:
            logger.info("Injeção detectada e bloqueada pelo banco de dados")
        self.assertTrue(User.objects.filter(username=self.username).exists())


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(SQLInjectionTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
