# Imagem customizada do Airflow — Trabalho 3 (IPCA + MLflow)
# Pacotes exigidos: mlflow, scikit-learn, pandas, requests, pendulum
FROM apache/airflow:2.10.3-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    mlflow==2.17.2 \
    scikit-learn==1.5.2 \
    pandas==2.2.3 \
    requests==2.32.3 \
    pendulum==3.0.0 \
    psycopg2-binary==2.9.10
