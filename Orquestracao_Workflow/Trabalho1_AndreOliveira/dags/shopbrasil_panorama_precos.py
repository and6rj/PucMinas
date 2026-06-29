"""
=============================================================================
DAG: shopbrasil_panorama_precos
ShopBrasil — Panorama diário de preços por categoria

Contexto:
  Marketplace em crescimento. Todo dia, antes do expediente, pricing e
  gerentes de categoria consultam um painel com preço médio, mínimo,
  máximo e quantidade de produtos por categoria. Hoje isso depende de
  um script Python agendado via cron sobre a API de catálogo.

Situação problema:
  - Falhas silenciosas quando a API oscila de madrugada
  - Reexecução manual gera dados duplicados
  - Nova categoria exige editar o código linha a linha
  - Arquitetura frágil, difícil de escalar e de operar

Objetivo:
  Substituir o cron por um pipeline Apache Airflow modular e legível,
  usando a FakeStore API como catálogo e PostgreSQL como base analítica.

Requisitos do pipeline:
  - Rodar todo dia às 06:00 (America/Sao_Paulo)
  - Resistir a instabilidades da API (retries + backoff)
  - Escalar automaticamente com novas categorias
  - Nunca duplicar dados em reprocessamento
  - Alertar quando algo falhar

Fonte de dados:
  - FakeStore API: https://fakestoreapi.com/docs
  - Endpoint principal: GET /products

Destino:
  - PostgreSQL analítico (connection postgres_lab → labdb)

Agendamento:
  - Cron: 0 6 * * * (todo dia às 06:00)
  - Timezone: America/Sao_Paulo (pendulum) — ancora start_date e schedule
  - start_date: 2024-01-01 (TZ Brasília)
  - catchup: False — não executa runs passadas

Topologias (identificáveis no Graph view):
  TaskGroup ingestao : buscar_produtos → validar_produtos → listar_categorias
  TaskGroup analise  : calcular_metricas.expand → consolidar → carregar → verificar
  FAN-OUT  : calcular_metricas.expand(categoria=…) — pool ecommerce_pool (2 slots)
  FAN-IN   : consolidar — reúne métricas das mapped tasks

XCom (TaskFlow API):
  Cada task retorna dados pequenos; o Airflow persiste automaticamente
  no XCom e injeta na task downstream via argumento da função.
  Contratos tipados em plugins/shopbrasil/schemas.py

Configurações para explorar na UI:
  - Gantt chart: Admin → DAGs → shopbrasil_panorama_precos → Gantt
  - XComs:       Admin → XComs
  - Logs:        clicar em qualquer task → Log

Status: Pipeline completo — carga idempotente + verificação pós-carga.
=============================================================================
"""

from __future__ import annotations

import logging

from airflow.decorators import dag, task, task_group
from airflow.timetables.trigger import CronTriggerTimetable

from shopbrasil.callbacks import (
    on_failure_callback,
    on_retry_callback,
    on_success_callback,
)
from shopbrasil.config import (
    API_REQUEST_TIMEOUT,
    CATCHUP,
    DEFAULT_ARGS,
    ECOMMERCE_POOL,
    FAKESTORE_PRODUCTS_URL,
    POSTGRES_CONN_ID,
    SCHEDULE_CRON,
    START_DATE,
    TZ,
)
from shopbrasil.schemas import MetricaCategoria, ProdutoResumo

log = logging.getLogger(__name__)


# =============================================================================
# DAG
# =============================================================================

@dag(
    dag_id="shopbrasil_panorama_precos",
    description=(
        "ShopBrasil: FakeStore API → métricas de preço por categoria → PostgreSQL"
    ),
    schedule=CronTriggerTimetable(SCHEDULE_CRON, timezone=TZ),
    start_date=START_DATE,
    catchup=CATCHUP,
    default_args=DEFAULT_ARGS,
    tags=["shopbrasil", "pricing", "etl", "fakestore"],
    doc_md=__doc__,
    max_active_runs=1,
)
def shopbrasil_panorama_precos():
    """
    Pipeline modular ShopBrasil — panorama de preços por categoria.

    TaskFlow API:
      - Dependências = chamadas entre funções (retorno → argumento).
      - XCom automático via return (apenas payloads pequenos; ver schemas.py).

    Topologias:
      TaskGroup ingestao → coleta, validação e categorias
      TaskGroup analise  → fan-out/fan-in, carga e verificação
    """

    # =========================================================================
    # TaskGroup: INGESTÃO — coleta e preparação do catálogo
    # =========================================================================
    @task_group(group_id="ingestao", tooltip="Coleta FakeStore API, validação e categorias")
    def ingestao():
        @task(
            task_id="buscar_produtos",
            on_success_callback=on_success_callback,
            on_failure_callback=on_failure_callback,
            on_retry_callback=on_retry_callback,
        )
        def buscar_produtos() -> list[ProdutoResumo]:
            """
            Busca catálogo de produtos na FakeStore API (gratuita, sem autenticação).

            Retorna:
                list[ProdutoResumo] com id, price e category por produto
            """
            import requests  # importar dentro da task = isolamento correto

            resultados = []

            log.info("Buscando produtos na FakeStore API: %s", FAKESTORE_PRODUCTS_URL)

            try:
                response = requests.get(
                    FAKESTORE_PRODUCTS_URL,
                    timeout=API_REQUEST_TIMEOUT,
                )
                response.raise_for_status()     # lança exceção em erro HTTP

                produtos_brutos = response.json()

                if not isinstance(produtos_brutos, list) or len(produtos_brutos) == 0:
                    raise ValueError(
                        "FakeStore API retornou catálogo vazio ou formato inesperado"
                    )

                for produto in produtos_brutos:
                    resumo = ProdutoResumo(
                        id=int(produto["id"]),
                        price=float(produto["price"]),
                        category=str(produto["category"]),
                    )
                    resultados.append(resumo)

                    log.info(
                        "✓ produto id=%d — categoria=%s — preço=%.2f",
                        resumo["id"],
                        resumo["category"],
                        resumo["price"],
                    )

            except requests.RequestException as e:
                log.error("Erro HTTP ao consultar FakeStore API: %s", e)
                raise
            except (ValueError, KeyError, TypeError) as e:
                log.error("Erro ao processar resposta da FakeStore API: %s", e)
                raise

            log.info("Total de produtos coletados: %d", len(resultados))
            return resultados

        @task(task_id="validar_produtos")
        def validar_produtos(produtos: list[ProdutoResumo]) -> list[ProdutoResumo]:
            """Valida integridade dos produtos antes de agregar métricas."""
            from shopbrasil.validate import validate_products

            log.info("Iniciando validação de %d produtos", len(produtos))

            try:
                validados = validate_products(produtos)
            except ValueError as e:
                log.error("Erro na validação de produtos: %s", e)
                raise

            log.info("Total de produtos validados: %d", len(validados))
            return validados

        @task(task_id="listar_categorias")
        def listar_categorias(produtos: list[ProdutoResumo]) -> list[str]:
            """Descobre categorias em runtime — alimenta o fan-out."""
            from shopbrasil.categories import list_categories

            log.info("Listando categorias a partir de %d produtos", len(produtos))

            try:
                categorias = list_categories(produtos)
            except ValueError as e:
                log.error("Erro ao listar categorias: %s", e)
                raise

            log.info("Categorias para fan-out: %s", categorias)
            return categorias

        produtos = buscar_produtos()
        produtos_validados = validar_produtos(produtos)
        categorias = listar_categorias(produtos_validados)

        return produtos_validados, categorias

    # =========================================================================
    # TaskGroup: ANÁLISE — métricas paralelas, consolidação e publicação
    # =========================================================================
    @task_group(
        group_id="analise",
        tooltip="Métricas por categoria (fan-out/fan-in) e carga analítica",
    )
    def analise(
        produtos_validados: list[ProdutoResumo],
        categorias: list[str],
    ):
        @task(task_id="calcular_metricas", pool=ECOMMERCE_POOL)
        def calcular_metricas(
            produtos: list[ProdutoResumo],
            categoria: str,
        ) -> MetricaCategoria:
            """Calcula métricas de UMA categoria (dynamic task mapping)."""
            from shopbrasil.transform import calculate_category_metrics

            log.info(
                "Calculando métricas — categoria=%s | pool=%s",
                categoria,
                ECOMMERCE_POOL,
            )

            try:
                metricas = calculate_category_metrics(produtos, categoria)
            except ValueError as e:
                log.error("Erro ao calcular métricas de '%s': %s", categoria, e)
                raise

            return metricas

        @task(task_id="consolidar")
        def consolidar(metricas: list[MetricaCategoria]) -> list[MetricaCategoria]:
            """Fan-in: reúne métricas de todas as categorias."""
            from shopbrasil.transform import consolidate_metrics

            consolidado = consolidate_metrics(metricas)
            log.info("Métricas consolidadas: %s", [m["categoria"] for m in consolidado])
            return consolidado

        @task(task_id="carregar")
        def carregar(registros: list[MetricaCategoria], **context) -> int:
            """
            Persiste métricas no PostgreSQL via PostgresHook (connection postgres_lab).

            Idempotência: DELETE + INSERT por data_referencia — re-run não duplica.
            """
            from shopbrasil.load import upsert_daily_metrics

            run_id = context["run_id"]
            data_referencia = context["ds"]

            log.info(
                "Gravando %d registros — connection=%s | data=%s",
                len(registros),
                POSTGRES_CONN_ID,
                data_referencia,
            )

            try:
                total = upsert_daily_metrics(
                    registros=registros,
                    data_referencia=data_referencia,
                    run_id=run_id,
                )
            except Exception as e:
                log.error("Erro ao gravar no PostgreSQL: %s", e)
                raise

            return total

        @task(task_id="verificar")
        def verificar(total_inserido: int, **context) -> None:
            """
            Valida integridade pós-carga — qualidade de dados em produção.

            Confere que os registros gravados batem com o total retornado por carregar.
            """
            from shopbrasil.load import verify_daily_metrics

            verify_daily_metrics(
                total_inserido=total_inserido,
                data_referencia=context["ds"],
                run_id=context["run_id"],
            )

        metricas_por_categoria = calcular_metricas.partial(
            produtos=produtos_validados,
        ).expand(categoria=categorias)

        metricas = consolidar(metricas_por_categoria)
        total = carregar(metricas)
        verificar(total)

    # =========================================================================
    # Pipeline — TaskGroups encadeados via TaskFlow API
    # =========================================================================
    produtos_validados, categorias = ingestao()
    analise(produtos_validados, categorias)


dag_instance = shopbrasil_panorama_precos()
