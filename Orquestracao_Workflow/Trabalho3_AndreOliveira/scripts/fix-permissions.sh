#!/usr/bin/env bash
# Corrige permissões dos logs do Airflow (rode se aparecer PermissionError).
set -euo pipefail

cd "$(dirname "$0")"
UID_LOCAL="${AIRFLOW_UID:-$(id -u)}"

echo "AIRFLOW_UID=${UID_LOCAL}" > .env
grep -q '_AIRFLOW_WWW_USER_USERNAME' .env || echo "_AIRFLOW_WWW_USER_USERNAME=admin" >> .env
grep -q '_AIRFLOW_WWW_USER_PASSWORD' .env || echo "_AIRFLOW_WWW_USER_PASSWORD=admin" >> .env

docker run --rm --user root \
  -v "$(pwd)/logs:/opt/airflow/logs" \
  -v "$(pwd)/dags:/opt/airflow/dags" \
  -v "$(pwd)/plugins:/opt/airflow/plugins" \
  trabalho3-airflow:latest \
  bash -c "chown -R ${UID_LOCAL}:0 /opt/airflow/{logs,dags,plugins} && find /opt/airflow/logs -type d -exec chmod 777 {} + && find /opt/airflow/logs -type f -exec chmod 666 {} + 2>/dev/null || true"

echo "Permissões corrigidas. Reinicie: docker compose up -d --scale airflow-worker=3"
