#!/usr/bin/env bash
# Recria tabelas sem SERIAL — corrige persistir_raw (permission denied for sequence)
set -euo pipefail
cd "$(dirname "$0")/.."
docker exec -i trabalho3-postgres psql -U postgres -d ipca < sql/migrate_remove_serial.sql
echo "Tabelas recriadas. No Airflow: Clear em persistir_raw + Trigger DAG."
