-- =============================================================================
-- Lab Airflow — Aula 1
-- Inicialização do banco de dados de destino (postgres-lab)
-- Este script roda automaticamente na primeira vez que o container sobe
-- =============================================================================

-- Tabela principal onde o DAG vai inserir os dados de clima
CREATE TABLE IF NOT EXISTS clima (
    id          SERIAL PRIMARY KEY,
    cidade      VARCHAR(100) NOT NULL,
    latitude    NUMERIC(8, 4),
    longitude   NUMERIC(8, 4),
    hora        TIMESTAMP NOT NULL,
    temperatura_c NUMERIC(5, 2),
    dag_run_id  VARCHAR(250),          -- rastreabilidade: qual run gerou o registro
    inserido_em TIMESTAMP DEFAULT NOW()
);

-- Índice para consultas por cidade e hora
CREATE INDEX IF NOT EXISTS idx_clima_cidade_hora ON clima (cidade, hora);

-- Tabela de log de execuções (usada na extensão do lab)
CREATE TABLE IF NOT EXISTS etl_log (
    id          SERIAL PRIMARY KEY,
    dag_id      VARCHAR(250),
    run_id      VARCHAR(250),
    task_id     VARCHAR(250),
    status      VARCHAR(50),
    registros   INTEGER DEFAULT 0,
    mensagem    TEXT,
    criado_em   TIMESTAMP DEFAULT NOW()
);

-- View útil para inspecionar os dados inseridos
CREATE OR REPLACE VIEW v_clima_resumo AS
SELECT
    cidade,
    DATE(hora)          AS data,
    COUNT(*)            AS total_horas,
    ROUND(MIN(temperatura_c)::numeric, 1) AS temp_min,
    ROUND(MAX(temperatura_c)::numeric, 1) AS temp_max,
    ROUND(AVG(temperatura_c)::numeric, 1) AS temp_media
FROM clima
GROUP BY cidade, DATE(hora)
ORDER BY cidade, data DESC;

-- =============================================================================
-- ShopBrasil — panorama de preços por categoria
-- =============================================================================

CREATE TABLE IF NOT EXISTS precos_categoria (
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
);

CREATE INDEX IF NOT EXISTS idx_precos_categoria_data
    ON precos_categoria (data_referencia DESC);

CREATE OR REPLACE VIEW v_precos_categoria_painel AS
SELECT
    data_referencia,
    categoria,
    preco_medio,
    preco_min,
    preco_max,
    qtd_produtos,
    dag_run_id,
    inserido_em
FROM precos_categoria
ORDER BY data_referencia DESC, categoria;

-- Permissões
GRANT ALL ON ALL TABLES IN SCHEMA public TO lab;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO lab;
GRANT SELECT ON v_clima_resumo TO lab;
GRANT SELECT ON v_precos_categoria_painel TO lab;

-- Mensagem de confirmação
DO $$ BEGIN
    RAISE NOTICE 'Banco labdb inicializado com sucesso!';
    RAISE NOTICE 'Tabelas: clima, etl_log, precos_categoria | Views: v_clima_resumo, v_precos_categoria_painel';
END $$;
