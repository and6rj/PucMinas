import numpy as np
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema
import mlflow
from sklearn.datasets import load_wine

# ── 1. Schema de validação ────────────────────────────────────
# API correta do Pandera: pa.Check (não pa.checks.InRangeCheck — não existe)
schema = DataFrameSchema({
    "alcohol": Column(float, checks=pa.Check.in_range(8.0, 16.0)),
    "malic_acid": Column(float, checks=pa.Check.greater_than_or_equal_to(0.0)),
    "ash": Column(float, checks=pa.Check.greater_than_or_equal_to(0.0)),
    "alcalinity_of_ash": Column(float, checks=pa.Check.in_range(0.0, 50.0)),
})

# ── 2. Carregar dados ─────────────────────────────────────────
wine = load_wine()
colunas = ["alcohol", "malic_acid", "ash", "alcalinity_of_ash"]
df = pd.DataFrame(wine.data, columns=wine.feature_names)[colunas]
print(f"Dataset: {df.shape[0]} linhas, {df.shape[1]} colunas")
print(df.describe().round(2))

# ── 3. Validar ────────────────────────────────────────────────
mlflow.set_experiment("wine-classification")
with mlflow.start_run(run_name="data-validation"):
    try:
        schema.validate(df)
        print("\n✓ Dados válidos — todos os checks passaram")
        mlflow.log_param("data_validation", "passed")
        mlflow.log_metric("n_rows", len(df))
        mlflow.log_metric("n_cols", len(df.columns))
    except pa.errors.SchemaError as e:
        print(f"\n✗ Dados inválidos: {e}")
        mlflow.log_param("data_validation", "failed")
        mlflow.log_param("validation_error", str(e)[:250])
        raise

# ── 4. Demonstrar falha intencional ──────────────────────────
print("\n--- Demonstração: dados com valor inválido ---")
df_invalido = df.copy()
df_invalido.loc[0, "alcohol"] = 99.0  # fora do range 8-16
with mlflow.start_run(run_name="data-validation-failed"):
    try:
        schema.validate(df_invalido)
    except pa.errors.SchemaError as e:
        print(f"✗ Schema rejeitou os dados (esperado): {e}")
        mlflow.log_param("data_validation", "failed")
        mlflow.log_param("validation_error", str(e)[:250])
