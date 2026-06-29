"""Descoberta de categorias em runtime — alimenta o fan-out do pipeline."""

from __future__ import annotations

import logging

from shopbrasil.schemas import ProdutoResumo

log = logging.getLogger(__name__)


def list_categories(produtos: list[ProdutoResumo]) -> list[str]:
    """
    Extrai categorias únicas dos produtos validados.

    Returns:
        Lista ordenada de nomes de categoria (sem hardcode).
    """
    if not produtos:
        raise ValueError("Nenhum produto recebido para listar categorias")

    categorias = sorted({produto["category"] for produto in produtos})

    if not categorias:
        raise ValueError("Nenhuma categoria encontrada nos produtos validados")

    for categoria in categorias:
        qtd = sum(1 for p in produtos if p["category"] == categoria)
        log.info("✓ categoria=%s — %d produto(s)", categoria, qtd)

    log.info("Total de categorias listadas: %d", len(categorias))
    return categorias
