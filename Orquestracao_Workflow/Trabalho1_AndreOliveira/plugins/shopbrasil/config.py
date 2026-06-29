"""
Configurações centralizadas — pipeline ShopBrasil.

Fonte de dados : FakeStore API (https://fakestoreapi.com/docs)
Destino        : PostgreSQL analítico (connection postgres_lab / labdb)
"""

from datetime import timedelta

import pendulum

# =============================================================================
# FakeStore API — catálogo de produtos
# Documentação: https://fakestoreapi.com/docs
# =============================================================================

FAKESTORE_API_BASE = "https://fakestoreapi.com"

# Endpoints utilizados pelo pipeline
FAKESTORE_PRODUCTS_URL = f"{FAKESTORE_API_BASE}/products"
FAKESTORE_CATEGORIES_URL = f"{FAKESTORE_API_BASE}/products/categories"

# Campos esperados em cada produto (contrato da API)
PRODUTO_CAMPOS_OBRIGATORIOS = ("id", "title", "price", "category")

# Timeout HTTP para chamadas à API (segundos)
API_REQUEST_TIMEOUT = 30

# =============================================================================
# PostgreSQL analítico — docker-compose (serviço postgres-lab)
# Connection criada automaticamente pelo airflow-init:
#   host=postgres-lab | login=lab | password=lab123 | schema=labdb | port=5432
# Inspeção externa: localhost:5433
# =============================================================================

POSTGRES_CONN_ID = "postgres_lab"
POSTGRES_DB = "labdb"
POSTGRES_USER = "lab"

# Tabela de destino (será criada no passo de carga)
TABLE_PRECOS_CATEGORIA = "precos_categoria"

# Pool para limitar concorrência das tasks mapeadas (fan-out)
ECOMMERCE_POOL = "ecommerce_pool"
ECOMMERCE_POOL_SLOTS = 2
ECOMMERCE_POOL_DESCRIPTION = (
    "ShopBrasil — processamento paralelo de métricas por categoria (max 2 simultâneas)"
)

# =============================================================================
# Agendamento — timezone ancorado em America/Sao_Paulo (pendulum)
# =============================================================================

TZ = pendulum.timezone("America/Sao_Paulo")
SCHEDULE_CRON = "0 6 * * *"  # todo dia às 06:00 (horário de Brasília)
START_DATE = pendulum.datetime(2024, 1, 1, tz=TZ)  # início do histórico do DAG
CATCHUP = False  # não reprocessa runs passadas ao ativar/reagendar

# Alias legível (compatível com imports existentes)
TIMEZONE = "America/Sao_Paulo"

DEFAULT_ARGS = {
    "owner": "shopbrasil_data",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,   # 2min → 4min → 8min
    "execution_timeout": timedelta(minutes=30),
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}
