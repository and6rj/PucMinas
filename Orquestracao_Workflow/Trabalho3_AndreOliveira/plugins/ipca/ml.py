"""Treinamento MLflow e consolidação fan-in."""

from __future__ import annotations

import logging
import os
from typing import Any

import mlflow
import numpy as np
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from ipca.config import MLFLOW_TRACKING_URI, POSTGRES_CONN_ID

log = logging.getLogger(__name__)

EXPERIMENT_NAME = "ipca_alimentos_basicos"


def _tracking_uri() -> str:
    return os.environ.get("MLFLOW_TRACKING_URI", MLFLOW_TRACKING_URI)


def _carregar_series_agregadas() -> dict[str, pd.DataFrame]:
    """Lê dados agregados da camada Bronze agrupados por alimento."""
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    registros = hook.get_records(
        """
        SELECT mes_ano, codigo_alimento, produto, valor
        FROM bronze.raw_ipca
        ORDER BY codigo_alimento, mes_ano
        """
    )

    if not registros:
        raise ValueError("Nenhum dado encontrado em bronze.raw_ipca para treinamento")

    df = pd.DataFrame(
        registros,
        columns=["mes_ano", "codigo_alimento", "produto", "valor"],
    )
    df["valor"] = df["valor"].astype(float)

    series: dict[str, pd.DataFrame] = {}
    for codigo, grupo in df.groupby("codigo_alimento"):
        series[str(codigo)] = grupo.sort_values("mes_ano").reset_index(drop=True)

    return series


def treinar_modelos_agregados() -> list[dict[str, Any]]:
    """
    Task 3 (linear): treina regressão por produto e registra no MLflow.

    Retorna lista de métricas — insumo do fan-in na Task 4.
    """
    mlflow.set_tracking_uri(_tracking_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    series = _carregar_series_agregadas()
    metricas: list[dict[str, Any]] = []

    for codigo, df in series.items():
        if len(df) < 3:
            log.warning("Série insuficiente | codigo=%s", codigo)
            continue

        produto = str(df["produto"].iloc[-1])
        run_slug = produto.lower().replace(" ", "_")
        df = df.copy()
        df["t"] = np.arange(len(df))
        x = df[["t"]].values
        y = df["valor"].values

        split = max(1, len(x) - 1)
        x_train, y_train = x[:split], y[:split]
        x_test, y_test = x[split:], y[split:]

        with mlflow.start_run(run_name=f"treino_{run_slug}"):
            model = LinearRegression()
            model.fit(x_train, y_train)

            preds = model.predict(x_test) if len(x_test) else model.predict(x_train)
            target = y_test if len(y_test) else y_train
            rmse = float(np.sqrt(mean_squared_error(target, preds)))
            coef = float(model.coef_[0])
            tendencia = coef

            mlflow.log_param("codigo_alimento", codigo)
            mlflow.log_param("produto", produto)
            mlflow.log_param("modelo", "LinearRegression")
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("tendencia_coef", tendencia)
            mlflow.sklearn.log_model(model, artifact_path="model")

            run_id = mlflow.active_run().info.run_id
            metricas.append(
                {
                    "codigo_alimento": codigo,
                    "produto": produto,
                    "rmse": rmse,
                    "tendencia_alta": tendencia,
                    "mlflow_run_id": run_id,
                    "modelo": "LinearRegression",
                }
            )

            log.info(
                "Treino OK | produto=%s | rmse=%.4f | tendencia=%.4f",
                produto,
                rmse,
                tendencia,
            )

    if not metricas:
        raise ValueError("Nenhum modelo treinado — verifique bronze.raw_ipca")

    return metricas


def consolidar_alerta_inflacao(
    metricas: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    """
    Task 4 (fan-in): identifica maior tendência de alta e persiste alerta.

    Critério: maior coeficiente de regressão (tendência de alta mensal).
    """
    if not metricas:
        raise ValueError("Lista de métricas vazia no fan-in")

    campeao = max(metricas, key=lambda m: m["tendencia_alta"])

    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    hook.run(
        "DELETE FROM gold.tb_alerta_inflacao WHERE run_id = %s",
        parameters=(run_id,),
    )

    insert_sql = """
        INSERT INTO gold.tb_alerta_inflacao
            (codigo_alimento, produto, tendencia_alta, rmse, mlflow_run_id, run_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    hook.run(
        insert_sql,
        parameters=(
            campeao["codigo_alimento"],
            campeao["produto"],
            campeao["tendencia_alta"],
            campeao["rmse"],
            campeao["mlflow_run_id"],
            run_id,
        ),
    )

    relatorio = {
        "run_id": run_id,
        "alerta_produto": campeao["produto"],
        "alerta_codigo": campeao["codigo_alimento"],
        "tendencia_alta": campeao["tendencia_alta"],
        "rmse": campeao["rmse"],
        "total_produtos_avaliados": len(metricas),
    }
    log.info("Fan-in consolidado | alerta=%s | tendencia=%.4f", relatorio["alerta_produto"], relatorio["tendencia_alta"])
    return relatorio
