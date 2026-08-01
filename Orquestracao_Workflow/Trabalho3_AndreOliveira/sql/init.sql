-- PostgreSQL compartilhado: Airflow (metadados), MLflow (tracking) e Target DB (IPCA)
-- Executado automaticamente na primeira subida do container postgres.

CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;

CREATE USER mlflow WITH PASSWORD 'mlflow';
CREATE DATABASE mlflow OWNER mlflow;

CREATE USER ipca WITH PASSWORD 'ipca';
CREATE DATABASE ipca OWNER ipca;

\c ipca

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Bronze: PK composta (sem SERIAL — evita erro de permissão em sequence)
CREATE TABLE IF NOT EXISTS bronze.raw_ipca (
    mes_ano          VARCHAR(6)   NOT NULL,
    codigo_alimento  VARCHAR(20)  NOT NULL,
    produto          VARCHAR(255) NOT NULL,
    valor            NUMERIC(12, 4),
    payload_json     JSONB,
    ingested_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (mes_ano, codigo_alimento)
);

-- Gold: PK = run_id (sem SERIAL)
CREATE TABLE IF NOT EXISTS gold.tb_alerta_inflacao (
    codigo_alimento  VARCHAR(20)  NOT NULL,
    produto          VARCHAR(255) NOT NULL,
    tendencia_alta   NUMERIC(12, 4) NOT NULL,
    rmse             NUMERIC(12, 4),
    mlflow_run_id    VARCHAR(64),
    run_id           VARCHAR(64)  NOT NULL PRIMARY KEY,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze TO ipca;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA gold TO ipca;
GRANT USAGE, CREATE ON SCHEMA bronze, silver, gold TO ipca;

ALTER TABLE bronze.raw_ipca OWNER TO ipca;
ALTER TABLE gold.tb_alerta_inflacao OWNER TO ipca;
