"""Cálculo de métricas de preço por categoria."""

from __future__ import annotations

import logging

from shopbrasil.schemas import MetricaCategoria, ProdutoResumo

log = logging.getLogger(__name__)


def calculate_category_metrics(
    produtos: list[ProdutoResumo],
    categoria: str,
) -> MetricaCategoria:
    """
    Calcula preço médio, mínimo, máximo e quantidade para uma categoria.

    Args:
        produtos: Catálogo validado (partial do dynamic mapping).
        categoria: Nome da categoria (expand do dynamic mapping).
    """
    precos = [
        float(produto["price"])
        for produto in produtos
        if produto["category"] == categoria
    ]

    if not precos:
        raise ValueError(f"Nenhum produto encontrado para categoria '{categoria}'")

    metricas = MetricaCategoria(
        categoria=categoria,
        preco_medio=round(sum(precos) / len(precos), 2),
        preco_min=round(min(precos), 2),
        preco_max=round(max(precos), 2),
        qtd_produtos=len(precos),
    )

    log.info(
        "✓ %s — médio=%.2f | min=%.2f | max=%.2f | qtd=%d",
        categoria,
        metricas["preco_medio"],
        metricas["preco_min"],
        metricas["preco_max"],
        metricas["qtd_produtos"],
    )

    return metricas


def consolidate_metrics(metricas: list[MetricaCategoria]) -> list[MetricaCategoria]:
    """Fan-in: reúne métricas das mapped tasks em lista ordenada."""
    consolidado = sorted(metricas, key=lambda m: m["categoria"])
    log.info("Consolidadas métricas de %d categorias", len(consolidado))
    return consolidado
