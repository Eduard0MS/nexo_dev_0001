"""
Módulo para atualização automática do arquivo dados.json quando a base de dados for modificada.
Para ativar este módulo, adicione 'core.dados_json_update' ao INSTALLED_APPS no settings.py.
"""

import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from decimal import Decimal

from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Caminho para o arquivo JSON
ORGANOGRAMA_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "static", "data", "organograma.json"
)

# Variáveis de controle
atualizacao_pendente = False
ultima_atualizacao = None
lock = threading.Lock()


def decimal_para_float(obj):
    """Converter objetos Decimal para float para serialização JSON"""
    if isinstance(obj, Decimal):
        # Arredondar para duas casas decimais
        rounded_value = round(float(obj), 2)
        return rounded_value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def gerar_organograma_json():
    """
    Gera um arquivo JSON com dados das tabelas UnidadeCargo e CargoSIORG.
    """
    from core.models import UnidadeCargo, CargoSIORG

    print(f"[{datetime.now()}] Iniciando geração do arquivo organograma.json...")

    # Estrutura para armazenar os dados
    resultado = {"core_unidadecargo": [], "core_cargosiorg": []}

    # Primeiro, criar um dicionário de cargos para consulta rápida
    cargos_dict = {}

    # Obter todos os registros de CargoSIORG
    cargos_siorg = CargoSIORG.objects.all()
    print(
        f"[{datetime.now()}] Processando {cargos_siorg.count()} registros de CargoSIORG"
    )

    # Adicionar cada cargo ao resultado e ao dicionário para consulta rápida
    for cargo in cargos_siorg:
        cargo_dados = {"cargo": cargo.cargo, "nivel": cargo.nivel, "valor": cargo.valor}
        resultado["core_cargosiorg"].append(cargo_dados)

        # Adicionar ao dicionário para consultas rápidas
        cargos_dict[cargo.cargo] = {"nivel": cargo.nivel, "valor": cargo.valor}

    # Obter todos os registros de UnidadeCargo
    unidades_cargo = UnidadeCargo.objects.all()
    print(
        f"[{datetime.now()}] Processando {unidades_cargo.count()} registros de UnidadeCargo"
    )

    # Adicionar cada unidade de cargo ao resultado
    for unidade in unidades_cargo:
        # Formar a string de cargo para busca no dicionário de cargos
        cargo_string = None
        if (
            unidade.tipo_cargo
            and unidade.categoria is not None
            and unidade.nivel is not None
        ):
            cargo_string = f"{unidade.tipo_cargo} {unidade.categoria} {unidade.nivel}"

        # Valores padrão
        pontos = 0
        valor_unitario = 0
        gasto_total = 0

        # Buscar o valor e pontos no dicionário de cargos
        if cargo_string and cargo_string in cargos_dict:
            cargo_info = cargos_dict[cargo_string]
            pontos = cargo_info["nivel"]
            valor_unitario = cargo_info["valor"]

            # Calcular o gasto total
            if unidade.quantidade and valor_unitario:
                try:
                    gasto_total = float(valor_unitario) * unidade.quantidade
                except (ValueError, TypeError):
                    print(
                        f"[{datetime.now()}] Erro ao calcular gasto para: {unidade.codigo_unidade} - {cargo_string}"
                    )

        unidade_dados = {
            "tipo_unidade": unidade.tipo_unidade,
            "denominacao_unidade": unidade.denominacao_unidade,
            "codigo_unidade": unidade.codigo_unidade,
            "sigla": unidade.sigla_unidade,
            "tipo_cargo": unidade.tipo_cargo,
            "denominacao": unidade.denominacao,
            "categoria": unidade.categoria,
            "nivel": unidade.nivel,
            "quantidade": unidade.quantidade,
            "grafo": unidade.grafo,
            # Adicionando os campos calculados
            "pontos": pontos,
            "valor_unitario": valor_unitario,
            "gasto_total": gasto_total,
        }
        resultado["core_unidadecargo"].append(unidade_dados)

    # Salvar o resultado em JSON
    with open(ORGANOGRAMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            resultado, f, ensure_ascii=False, indent=2, default=decimal_para_float
        )

    print(
        f"[{datetime.now()}] Arquivo organograma.json gerado com sucesso em: {ORGANOGRAMA_JSON_PATH}"
    )
    print(
        f"[{datetime.now()}] Total de registros: {len(resultado['core_unidadecargo'])} unidades e {len(resultado['core_cargosiorg'])} cargos"
    )

    return resultado


@receiver(post_save, sender="core.UnidadeCargo")
@receiver(post_delete, sender="core.UnidadeCargo")
@receiver(post_save, sender="core.CargoSIORG")
@receiver(post_delete, sender="core.CargoSIORG")
def atualizar_json_ao_modificar_modelo(sender, **kwargs):
    """Sinaliza que uma atualização do arquivo JSON é necessária"""
    global atualizacao_pendente
    with lock:
        atualizacao_pendente = True
    print(
        f"[{datetime.now()}] Atualização de organograma.json sinalizada após modificação em {sender}"
    )


def verificar_e_atualizar_json():
    """Verifica periodicamente se é necessário atualizar o arquivo organograma.json"""
    global atualizacao_pendente, ultima_atualizacao

    while True:
        with lock:
            pendente = atualizacao_pendente
            if pendente:
                atualizacao_pendente = False

        if pendente:
            try:
                gerar_organograma_json()
                with lock:
                    ultima_atualizacao = datetime.now()
            except Exception as e:
                print(
                    f"[{datetime.now()}] Erro ao atualizar organograma.json: {str(e)}"
                )

        # Verificar a cada 30 segundos
        time.sleep(30)


class DadosJsonConfig(AppConfig):
    name = "core.dados_json_update"
    verbose_name = "Atualizador de Organograma JSON"

    def ready(self):
        """Inicializa o atualizador quando o Django estiver pronto"""
        # Evitar execução dupla em modo de desenvolvimento
        if os.environ.get("RUN_MAIN") != "true":
            # Gerar o arquivo JSON inicial se não existir
            if not Path(ORGANOGRAMA_JSON_PATH).exists():
                print(
                    f"[{datetime.now()}] Arquivo {ORGANOGRAMA_JSON_PATH} não encontrado. Gerando..."
                )
                gerar_organograma_json()
                global ultima_atualizacao
                ultima_atualizacao = datetime.now()

            # Iniciar thread de atualização
            thread = threading.Thread(target=verificar_e_atualizar_json, daemon=True)
            thread.start()
            print(
                f"[{datetime.now()}] Thread de atualização de organograma.json iniciada"
            )
