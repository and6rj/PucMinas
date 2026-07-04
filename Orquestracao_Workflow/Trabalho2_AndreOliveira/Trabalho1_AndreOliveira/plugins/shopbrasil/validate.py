"""Validação de qualidade dos produtos coletados na ingestão."""

from __future__ import annotations

import logging

from shopbrasil.schemas import ProdutoResumo

log = logging.getLogger(__name__)


def validate_products(produtos: list[ProdutoResumo]) -> list[ProdutoResumo]:
    """
    Valida integridade e regras de negócio de cada produto.

    Regras:
      - Catálogo não pode estar vazio
      - id deve ser inteiro positivo
      - price deve ser numérico e > 0
      - category não pode ser vazia

    Raises:
        ValueError: quando algum produto viola as regras
    """
    if not produtos:
        raise ValueError("Catálogo vazio — nenhum produto recebido da ingestão")

    validados: list[ProdutoResumo] = []

    for produto in produtos:
        produto_id = produto.get("id")
        preco = produto.get("price")
        categoria = produto.get("category")

        if produto_id is None or int(produto_id) <= 0:
            raise ValueError(f"Produto inválido: id={produto_id}")

        if preco is None or float(preco) <= 0:
            raise ValueError(f"Produto id={produto_id} com preço inválido: {preco}")

        if not categoria or not str(categoria).strip():
            raise ValueError(f"Produto id={produto_id} sem categoria")

        resumo = ProdutoResumo(
            id=int(produto_id),
            price=round(float(preco), 2),
            category=str(categoria).strip(),
        )
        validados.append(resumo)

        log.info(
            "✓ produto id=%d validado — categoria=%s — preço=%.2f",
            resumo["id"],
            resumo["category"],
            resumo["price"],
        )

    categorias = len({p["category"] for p in validados})
    log.info(
        "Validação OK — %d produtos, %d categorias",
        len(validados),
        categorias,
    )

    return validados
