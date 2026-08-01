-- Migração: remove colunas SERIAL (corrige persistir_raw sem depender de sequence)

DROP TABLE IF EXISTS bronze.raw_ipca CASCADE;

CREATE TABLE bronze.raw_ipca (
    mes_ano          VARCHAR(6)   NOT NULL,
    codigo_alimento  VARCHAR(20)  NOT NULL,
    produto          VARCHAR(255) NOT NULL,
    valor            NUMERIC(12, 4),
    payload_json     JSONB,
    ingested_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (mes_ano, codigo_alimento)
);

DROP TABLE IF EXISTS gold.tb_alerta_inflacao CASCADE;

CREATE TABLE gold.tb_alerta_inflacao (
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
ALTER TABLE bronze.raw_ipca OWNER TO ipca;
ALTER TABLE gold.tb_alerta_inflacao OWNER TO ipca;
