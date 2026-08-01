#!/usr/bin/env bash
# Limpa cache/logs do Airflow via serviço cache-clean do Compose e reinicializa a stack.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Executando cache-clean (logs, __pycache__, metadados Airflow, Redis, MLflow)..."
docker compose up cache-clean

echo "==> Reexecutando airflow-init (usuário admin + connections)..."
docker compose up airflow-init

echo ""
echo "Cache limpo. Suba a stack:"
echo "  docker compose up -d --scale airflow-worker=3"
