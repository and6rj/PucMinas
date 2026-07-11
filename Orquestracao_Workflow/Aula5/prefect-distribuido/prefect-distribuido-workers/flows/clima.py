"""
flows/clima.py — flow de exemplo para o repo distribuído.

Analisa o clima de várias cidades usando .map() (concorrência por threads).
É executado pelos workers; o registro do deployment fica em deploy.py.
"""

from datetime import datetime

import requests
from prefect import flow, task


@task(retries=2, retry_delay_seconds=30, log_prints=True)
def buscar_clima(cidade_info):
    """Busca dados de clima de uma cidade via API open-meteo."""
    cidade = cidade_info["nome"]
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": cidade_info["lat"],
        "longitude": cidade_info["lon"],
        "hourly": "temperature_2m,precipitation",
        "forecast_days": 1,
    }
    print(f"Buscando clima de {cidade}...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return {"cidade": cidade, "dados": response.json()}


@task(log_prints=True)
def processar_dados(resultado_fetch):
    """Extrai métricas a partir dos dados brutos."""
    cidade = resultado_fetch["cidade"]
    temps = resultado_fetch["dados"]["hourly"]["temperature_2m"]
    if not temps:
        raise ValueError(f"Sem dados de temperatura para {cidade}")
    metricas = {
        "cidade": cidade,
        "temperatura_media": round(sum(temps) / len(temps), 2),
        "temperatura_min": round(min(temps), 2),
        "temperatura_max": round(max(temps), 2),
        "timestamp": datetime.now().isoformat(),
    }
    print(f"{cidade}: media {metricas['temperatura_media']}C")
    return metricas


@task(log_prints=True)
def consolidar_resultados(lista_metricas):
    """Consolida as métricas de todas as cidades."""
    consolidado = {
        "cidades": list(lista_metricas),
        "total_cidades": len(lista_metricas),
        "timestamp_consolidacao": datetime.now().isoformat(),
    }
    print(f"Consolidado: {consolidado['total_cidades']} cidades")
    return consolidado


@flow(name="analise-clima", log_prints=True)
def analise_clima_multiplas_cidades():
    """Orquestra a análise de clima em concorrência via .map()."""
    CIDADES = [
        {"nome": "Sao Paulo", "lat": -23.5505, "lon": -46.6333},
        {"nome": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
        {"nome": "Belo Horizonte", "lat": -19.8267, "lon": -43.9345},
    ]
    dados_fetch = buscar_clima.map(CIDADES)
    metricas = processar_dados.map(dados_fetch)
    return consolidar_resultados(metricas)


if __name__ == "__main__":
    # teste local rápido (sem backend/worker)
    print(analise_clima_multiplas_cidades())
