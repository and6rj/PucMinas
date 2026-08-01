"""Callbacks de ciclo de vida — task crítica de ingestão SIDRA/IBGE."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def on_success_callback(context: dict[str, Any]) -> None:
    """Imprime no log o sucesso da operação de ingestão."""
    ti = context["task_instance"]
    log.info(
        "IPCA ✓ SUCESSO | ingestão SIDRA concluída | task=%s | dag=%s | run=%s | tentativa=%d",
        ti.task_id,
        ti.dag_id,
        ti.run_id,
        ti.try_number,
    )


def on_failure_callback(context: dict[str, Any]) -> None:
    """Imprime no log um alerta de falha na ingestão."""
    ti = context["task_instance"]
    exception = context.get("exception")
    log.error(
        "IPCA ✗ ALERTA DE FALHA | task=%s | dag=%s | run=%s | tentativa=%d | erro=%s",
        ti.task_id,
        ti.dag_id,
        ti.run_id,
        ti.try_number,
        exception,
    )


def on_retry_callback(context: dict[str, Any]) -> None:
    """Imprime no log um aviso de retentativa da ingestão."""
    ti = context["task_instance"]
    log.warning(
        "IPCA ↻ RETENTATIVA | task=%s | dag=%s | run=%s | tentativa=%d",
        ti.task_id,
        ti.dag_id,
        ti.run_id,
        ti.try_number,
    )
