"""Persistência raw no PostgreSQL — camada Bronze."""

from __future__ import annotations

import json
import logging
from typing import Any

from airflow.providers.postgres.hooks.postgres import PostgresHook

from ipca.config import POSTGRES_CONN_ID

log = logging.getLogger(__name__)


def persistir_raw_ipca(dados: dict[str, Any]) -> int:
    """
    Grava JSON bruto normalizado em bronze.raw_ipca via PostgresHook.

    Idempotência: INSERT ... ON CONFLICT (mes_ano, codigo_alimento) DO NOTHING.
    """
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    registros = dados["registros"]

    insert_sql = """
        INSERT INTO bronze.raw_ipca
            (mes_ano, codigo_alimento, produto, valor, payload_json)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (mes_ano, codigo_alimento) DO NOTHING
    """

    rows = [
        (
            r["mes_ano"],
            r["codigo_alimento"],
            r["produto"],
            r["valor"],
            json.dumps(r.get("payload_json", {})),
        )
        for r in registros
    ]

    conn = hook.get_conn()
    inseridos = 0
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(insert_sql, row)
                inseridos += cur.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    log.info(
        "Bronze raw_ipca | produto=%s | tentativas=%d | inseridos=%d",
        dados["produto"],
        len(rows),
        inseridos,
    )
    return inseridos
