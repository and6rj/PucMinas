"""Cliente da API SIDRA/IBGE — Tabela 7060 (IPCA)."""

from __future__ import annotations

import logging
from typing import Any

import requests

from ipca.config import (
    API_REQUEST_TIMEOUT,
    CODIGO_PARA_ALIMENTO,
    CODIGO_PARA_NOME,
    SIDRA_BASE_URL,
    SIDRA_PERIODOS,
    SIDRA_TABELA_IPCA,
    SIDRA_VARIAVEL_VARIACAO,
)

log = logging.getLogger(__name__)


def montar_url_sidra(codigo_sidra: str) -> str:
    """Endpoint SIDRA: t/7060, variação mensal (v63), últimos 36 meses."""
    periodos = SIDRA_PERIODOS.replace(" ", "%20")
    return (
        f"{SIDRA_BASE_URL}/t/{SIDRA_TABELA_IPCA}/n1/all"
        f"/v/{SIDRA_VARIAVEL_VARIACAO}/p/{periodos}"
        f"/c315/{codigo_sidra}/d/v{SIDRA_VARIAVEL_VARIACAO}%203"
    )


def _parse_valor(raw: str | None) -> float | None:
    if raw is None or raw in ("...", "-", ""):
        return None
    try:
        return float(str(raw).replace(",", "."))
    except ValueError:
        return None


def _parse_mes_ano(raw: str | None) -> str | None:
    if not raw:
        return None
    periodo = str(raw).strip()
    if len(periodo) == 6 and periodo.isdigit():
        return periodo
    return None


def _normalizar_registros(
    payload_json: list[dict[str, Any]],
    codigo_alimento: str,
    produto: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload_json, list) or len(payload_json) < 2:
        raise ValueError(f"SIDRA retornou resposta inválida para {produto}")

    registros: list[dict[str, Any]] = []
    for linha in payload_json[1:]:
        mes_ano = _parse_mes_ano(linha.get("D3C"))
        valor = _parse_valor(linha.get("V"))
        if mes_ano is None or valor is None:
            continue
        registros.append(
            {
                "mes_ano": mes_ano,
                "codigo_alimento": codigo_alimento,
                "produto": produto,
                "valor": valor,
                "payload_json": linha,
            }
        )
    return registros


def _obter_codigo_sidra(codigo_alimento: str) -> str:
    meta = CODIGO_PARA_ALIMENTO.get(codigo_alimento)
    if meta and meta.get("sidra_codigo"):
        return meta["sidra_codigo"]
    return codigo_alimento


def extrair_alimento_sidra(codigo_alimento: str) -> dict[str, Any]:
    """
    Extrai série de um alimento na API SIDRA.

    Usa o código c315 operacional (sidra_codigo) para obter valores numéricos.
    O codigo_alimento do enunciado é preservado nos registros persistidos.
    """
    produto = CODIGO_PARA_NOME.get(codigo_alimento, codigo_alimento)
    codigo_sidra = _obter_codigo_sidra(codigo_alimento)
    url = montar_url_sidra(codigo_sidra)

    log.info(
        "SIDRA | codigo=%s | sidra_codigo=%s | produto=%s | url=%s",
        codigo_alimento,
        codigo_sidra,
        produto,
        url,
    )

    try:
        response = requests.get(url, timeout=API_REQUEST_TIMEOUT)
        response.raise_for_status()
        payload_json = response.json()
    except requests.Timeout as exc:
        log.error("Timeout SIDRA | codigo=%s | %s", codigo_alimento, exc)
        raise
    except requests.RequestException as exc:
        log.error("Erro HTTP SIDRA | codigo=%s | %s", codigo_alimento, exc)
        raise
    except ValueError as exc:
        log.error("Erro ao decodificar JSON SIDRA | codigo=%s | %s", codigo_alimento, exc)
        raise

    registros = _normalizar_registros(payload_json, codigo_alimento, produto)
    if not registros:
        raise ValueError(f"Nenhum registro válido para {produto} ({codigo_alimento})")

    log.info("SIDRA OK | produto=%s | registros=%d", produto, len(registros))
    return {
        "codigo_alimento": codigo_alimento,
        "produto": produto,
        "registros": registros,
        "payload_json": payload_json,
    }
