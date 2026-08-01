"""Configurações compartilhadas — pipeline IPCA alimentos básicos."""

from __future__ import annotations

from datetime import timedelta

import pendulum

TZ = pendulum.timezone("America/Sao_Paulo")
START_DATE = pendulum.datetime(2025, 1, 1, tz=TZ)
CATCHUP = False
SCHEDULE = "@monthly"

POSTGRES_CONN_ID = "postgres_ipca"
MLFLOW_TRACKING_URI = "http://mlflow:5000"

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"
SIDRA_TABELA_IPCA = "7060"
SIDRA_VARIAVEL_VARIACAO = "63"
SIDRA_PERIODOS = "last 36"

# codigo = identificador pedido no enunciado (gravado no banco / MLflow)
# sidra_codigo = código c315 que retorna valores numéricos na API SIDRA
# (consulta direta por codigo do enunciato retorna V="..." na tabela 7060)
ALIMENTOS_BASICOS: list[dict[str, str]] = [
    {"codigo": "1101002", "nome": "Arroz", "sidra_codigo": "7173"},
    {"codigo": "1111015", "nome": "Leite", "sidra_codigo": "12393"},
    {"codigo": "1103003", "nome": "Batata", "sidra_codigo": "7202"},
    {"codigo": "1102069", "nome": "Pão Francês", "sidra_codigo": "7375"},
]

CODIGO_PARA_ALIMENTO: dict[str, dict[str, str]] = {
    item["codigo"]: item for item in ALIMENTOS_BASICOS
}

CODIGO_PARA_NOME: dict[str, str] = {
    item["codigo"]: item["nome"] for item in ALIMENTOS_BASICOS
}

API_REQUEST_TIMEOUT = 60

DEFAULT_ARGS = {
    "owner": "andre.oliveira",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
}
