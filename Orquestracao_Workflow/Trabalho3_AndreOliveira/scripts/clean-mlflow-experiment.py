#!/usr/bin/env python3
"""Remove experimento MLflow ipca_alimentos_basicos (hard delete) e artefatos."""

from __future__ import annotations

import os
import shutil
import sys

import psycopg2

BACKEND = os.environ.get(
    "MLFLOW_BACKEND_URI",
    "postgresql://mlflow:mlflow@postgres:5432/mlflow",
)
EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME", "ipca_alimentos_basicos")
ARTIFACTS_DIR = os.environ.get("MLFLOW_ARTIFACTS_DIR", "/mlflow/artifacts")

RUN_CHILD_TABLES = ("metrics", "params", "tags", "latest_metrics")


def main() -> int:
    conn = psycopg2.connect(BACKEND)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT experiment_id FROM experiments WHERE name = %s",
                (EXPERIMENT,),
            )
            row = cur.fetchone()
            if not row:
                print(f"Experimento MLflow não encontrado: {EXPERIMENT}")
                return 0

            exp_id = row[0]
            cur.execute(
                "SELECT run_uuid FROM runs WHERE experiment_id = %s",
                (exp_id,),
            )
            run_uuids = [r[0] for r in cur.fetchall()]

            for run_uuid in run_uuids:
                for table in RUN_CHILD_TABLES:
                    cur.execute(
                        f"DELETE FROM {table} WHERE run_uuid = %s",
                        (run_uuid,),
                    )

            cur.execute("DELETE FROM runs WHERE experiment_id = %s", (exp_id,))
            cur.execute(
                "DELETE FROM experiment_tags WHERE experiment_id = %s",
                (exp_id,),
            )
            cur.execute("DELETE FROM experiments WHERE experiment_id = %s", (exp_id,))
        conn.commit()
        print(
            f"Experimento MLflow removido (hard delete): {EXPERIMENT} "
            f"({len(run_uuids)} runs)"
        )
    finally:
        conn.close()

    if os.path.isdir(ARTIFACTS_DIR):
        for entry in os.listdir(ARTIFACTS_DIR):
            path = os.path.join(ARTIFACTS_DIR, entry)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        print(f"Artefatos MLflow limpos em {ARTIFACTS_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
