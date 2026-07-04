"""Callbacks de ciclo de vida — task crítica de ingestão ShopBrasil."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def _registrar_etl_log(
    context: dict[str, Any],
    status: str,
    mensagem: str,
    registros: int = 0,
) -> None:
    """Persiste evento operacional na tabela etl_log (best-effort)."""
    try:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        from shopbrasil.config import POSTGRES_CONN_ID

        ti = context["task_instance"]
        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        hook.run(
            """
            INSERT INTO etl_log (dag_id, run_id, task_id, status, registros, mensagem)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            parameters=(
                ti.dag_id,
                ti.run_id,
                ti.task_id,
                status,
                registros,
                mensagem[:2000],
            ),
        )
    except Exception as e:
        log.error("Não foi possível registrar callback em etl_log: %s", e)


def on_success_callback(context: dict[str, Any]) -> None:
    """Chamado quando a task crítica conclui com sucesso."""
    ti = context["task_instance"]
    log.info(
        "SHOPBRASIL ✓ SUCESSO | task=%s | run=%s | tentativa=%d",
        ti.task_id,
        ti.run_id,
        ti.try_number,
    )
    _registrar_etl_log(
        context,
        status="success",
        mensagem=f"Ingestão concluída na tentativa {ti.try_number}",
    )


def on_failure_callback(context: dict[str, Any]) -> None:
    """Chamado quando a task crítica falha definitivamente (retries esgotados)."""
    ti = context["task_instance"]
    exception = context.get("exception")
    mensagem = (
        f"Task {ti.task_id} falhou após {ti.try_number} tentativa(s): {exception}"
    )
    log.error("SHOPBRASIL ✗ FALHA | %s | run=%s", mensagem, ti.run_id)
    _registrar_etl_log(context, status="failure", mensagem=mensagem)


def on_retry_callback(context: dict[str, Any]) -> None:
    """Chamado antes de cada retry da task crítica."""
    ti = context["task_instance"]
    log.warning(
        "SHOPBRASIL ↻ RETRY | task=%s | tentativa=%d | run=%s",
        ti.task_id,
        ti.try_number,
        ti.run_id,
    )
    _registrar_etl_log(
        context,
        status="retry",
        mensagem=f"Retry #{ti.try_number} agendado para {ti.task_id}",
    )
