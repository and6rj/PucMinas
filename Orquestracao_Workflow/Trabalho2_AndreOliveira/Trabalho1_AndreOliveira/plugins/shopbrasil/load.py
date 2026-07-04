"""Persistência idempotente no PostgreSQL analítico — ShopBrasil."""

from __future__ import annotations

import logging

from shopbrasil.config import POSTGRES_CONN_ID, TABLE_PRECOS_CATEGORIA
from shopbrasil.schemas import MetricaCategoria

log = logging.getLogger(__name__)


def upsert_daily_metrics(
    registros: list[MetricaCategoria],
    data_referencia: str,
    run_id: str,
    postgres_conn_id: str = POSTGRES_CONN_ID,
    table: str = TABLE_PRECOS_CATEGORIA,
) -> int:
    """
    Grava métricas por categoria no PostgreSQL via PostgresHook.

    Idempotência: DELETE por data_referencia antes do INSERT —
    re-rodar a mesma run ou o mesmo dia não duplica linhas.

    Args:
        registros: Métricas consolidadas (fan-in).
        data_referencia: Data lógica da execução (context['ds']).
        run_id: Identificador do DAG run (rastreabilidade).
        postgres_conn_id: Connection Airflow (postgres_lab).

    Returns:
        Quantidade de linhas inseridas.
    """
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    if not registros:
        raise ValueError("Nenhum registro recebido para carga no PostgreSQL")

    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id              SERIAL PRIMARY KEY,
                data_referencia DATE NOT NULL,
                categoria       VARCHAR(100) NOT NULL,
                preco_medio     NUMERIC(10, 2) NOT NULL,
                preco_min       NUMERIC(10, 2) NOT NULL,
                preco_max       NUMERIC(10, 2) NOT NULL,
                qtd_produtos    INTEGER NOT NULL,
                dag_run_id      VARCHAR(250),
                inserido_em     TIMESTAMP DEFAULT NOW(),
                UNIQUE (data_referencia, categoria)
            )
            """
        )

        cur.execute(
            f"DELETE FROM {table} WHERE data_referencia = %s",
            (data_referencia,),
        )
        deletados = cur.rowcount
        if deletados > 0:
            log.info(
                "Idempotência: %d registros removidos para %s",
                deletados,
                data_referencia,
            )

        insert_sql = f"""
            INSERT INTO {table} (
                data_referencia, categoria, preco_medio,
                preco_min, preco_max, qtd_produtos, dag_run_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = [
            (
                data_referencia,
                registro["categoria"],
                registro["preco_medio"],
                registro["preco_min"],
                registro["preco_max"],
                registro["qtd_produtos"],
                run_id,
            )
            for registro in registros
        ]
        cur.executemany(insert_sql, valores)
        conn.commit()

        total = len(valores)
        log.info(
            "✓ %d registros inseridos em '%s' | data=%s | run_id=%s",
            total,
            table,
            data_referencia,
            run_id,
        )
        return total

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def verify_daily_metrics(
    total_inserido: int,
    data_referencia: str,
    run_id: str,
    postgres_conn_id: str = POSTGRES_CONN_ID,
    table: str = TABLE_PRECOS_CATEGORIA,
) -> None:
    """
    Valida que a carga foi persistida corretamente no PostgreSQL.

    Raises:
        ValueError: se a contagem no banco divergir do total informado.
    """
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    hook = PostgresHook(postgres_conn_id=postgres_conn_id)

    count = hook.get_first(
        f"""
        SELECT COUNT(*)
        FROM {table}
        WHERE data_referencia = %s AND dag_run_id = %s
        """,
        parameters=(data_referencia, run_id),
    )[0]

    log.info("=== VERIFICAÇÃO SHOPBRASIL ===")
    log.info(
        "Registros para %s (run %s): %d (esperado: %d)",
        data_referencia,
        run_id,
        count,
        total_inserido,
    )

    if count != total_inserido:
        raise ValueError(
            f"Verificação falhou: inseridos={total_inserido}, encontrados={count}"
        )

    resumo = hook.get_records(
        f"""
        SELECT categoria, preco_medio, preco_min, preco_max, qtd_produtos
        FROM {table}
        WHERE data_referencia = %s AND dag_run_id = %s
        ORDER BY categoria
        """,
        parameters=(data_referencia, run_id),
    )
    for categoria, medio, minimo, maximo, qtd in resumo:
        log.info(
            "  %s | médio=%.2f | min=%.2f | max=%.2f | qtd=%d",
            categoria,
            medio,
            minimo,
            maximo,
            qtd,
        )

    log.info("✓ Verificação OK — painel pronto para o time de pricing")
