"""
=============================================================================
DAG: inflacao_alimentos_mlops
Monitoramento de inflação de alimentos básicos — IPCA (IBGE SIDRA)

Topologias:
  Fase 1 — Fan-out : extrair_alimento.expand → persistir_raw.expand
  Fase 2 — Linear  : treinar_modelo (MLflow)
  Fase 3 — Fan-in  : consolidar_alerta (tb_alerta_inflacao)

Agendamento:
  - schedule: @monthly (dia 1, America/Sao_Paulo)
  - start_date: 2024-01-01 | catchup: False

XCom: return automático das funções @task
Callbacks: extrair_alimento (ingestão crítica)
=============================================================================
"""

from __future__ import annotations

import logging

from airflow.decorators import dag, task
from airflow.timetables.trigger import CronTriggerTimetable

from ipca.callbacks import (
    on_failure_callback,
    on_retry_callback,
    on_success_callback,
)
from ipca.config import ALIMENTOS_BASICOS, CATCHUP, DEFAULT_ARGS, START_DATE, TZ

log = logging.getLogger(__name__)


@dag(
    dag_id="inflacao_alimentos_mlops",
    description="IPCA alimentos: SIDRA fan-out → MLflow linear → alerta fan-in",
    schedule=CronTriggerTimetable("0 0 1 * *", timezone=TZ),
    start_date=START_DATE,
    catchup=CATCHUP,
    default_args=DEFAULT_ARGS,
    tags=["ipca", "ibge", "sidra", "mlops", "inflacao", "fan-out", "fan-in"],
    doc_md=__doc__,
    max_active_runs=1,
)
def inflacao_alimentos_mlops():
    """
    Pipeline MLOps com três topologias explícitas no Graph view.

    Fase 1 — Fan-out (Celery workers em paralelo):
      Task 1: extrair_alimento.expand(codigo) — mapeamento dinâmico SIDRA
      Task 2: persistir_raw.expand(dados)    — gravação raw idempotente

    Fase 2 — Linear:
      Task 3: treinar_modelo — lê Bronze, treina por produto, MLflow, retorna métricas

    Fase 3 — Fan-in:
      Task 4: consolidar_alerta — recebe array de métricas, salva tb_alerta_inflacao
    """

    # -------------------------------------------------------------------------
    # Fase 1 — Fan-out: extração descentralizada + persistência raw
    # -------------------------------------------------------------------------
    @task(
        task_id="extrair_alimento",
        on_success_callback=on_success_callback,
        on_failure_callback=on_failure_callback,
        on_retry_callback=on_retry_callback,
    )
    def extrair_alimento(codigo: str) -> dict:
        """
        Task 1 — Mapeamento dinâmico (fan-out).

        Cada alimento roda em worker Celery independente; falha isolada
        aciona retry apenas da instância mapeada (raise após try/except).
        """
        from ipca.sidra import extrair_alimento_sidra

        try:
            payload = extrair_alimento_sidra(codigo)
        except Exception as exc:
            log.error("Falha na extração | codigo=%s | erro=%s", codigo, exc)
            raise

        log.info(
            "Extração OK | codigo=%s | produto=%s | registros=%d",
            payload["codigo_alimento"],
            payload["produto"],
            len(payload["registros"]),
        )
        return payload

    @task(task_id="persistir_raw")
    def persistir_raw(dados: dict) -> int:
        """
        Task 2 — Persistência raw (fan-out paralelo à extração).

        PostgresHook + ON CONFLICT DO NOTHING (mes_ano, codigo_alimento).
        """
        from ipca.load import persistir_raw_ipca

        total = persistir_raw_ipca(dados)
        log.info("Persistência raw | produto=%s | inseridos=%d", dados["produto"], total)
        return total

    codigos = [item["codigo"] for item in ALIMENTOS_BASICOS]
    dados_extraidos = extrair_alimento.expand(codigo=codigos)
    totais_inseridos = persistir_raw.expand(dados=dados_extraidos)

    # -------------------------------------------------------------------------
    # Fase 2 — Linear: treinamento agregado + MLflow
    # -------------------------------------------------------------------------
    @task(task_id="treinar_modelo")
    def treinar_modelo(_inseridos: list[int]) -> list[dict]:
        """
        Task 3 — Treinamento linear (após fan-out concluir).

        Lê dados agregados do PostgreSQL, treina regressão por produto,
        registra codigo_alimento, modelo e RMSE no MLflow.
        Retorna array de métricas via XCom para o fan-in.
        """
        from ipca.ml import treinar_modelos_agregados

        metricas = treinar_modelos_agregados()
        log.info("Treinamento linear concluído | modelos=%d", len(metricas))
        return metricas

    metricas_produtos = treinar_modelo(totais_inseridos)

    # -------------------------------------------------------------------------
    # Fase 3 — Fan-in: consolidação do alerta de inflação
    # -------------------------------------------------------------------------
    @task(task_id="consolidar_alerta")
    def consolidar_alerta(metricas: list[dict], **context) -> dict:
        """
        Task 4 — Fan-in.

        Recebe o array de métricas de todos os produtos (Task 3),
        identifica a maior tendência de alta e grava gold.tb_alerta_inflacao.
        """
        from ipca.ml import consolidar_alerta_inflacao

        relatorio = consolidar_alerta_inflacao(
            metricas=metricas,
            run_id=context["run_id"],
        )
        log.info("Alerta de inflação | produto=%s", relatorio["alerta_produto"])
        return relatorio

    consolidar_alerta(metricas_produtos)


dag_instance = inflacao_alimentos_mlops()
