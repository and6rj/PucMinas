"""Integração com a FakeStore API — ingestão do catálogo de produtos."""

from __future__ import annotations

import logging

from shopbrasil.config import API_REQUEST_TIMEOUT, FAKESTORE_PRODUCTS_URL
from shopbrasil.schemas import ProdutoResumo

log = logging.getLogger(__name__)


def fetch_catalog() -> list[ProdutoResumo]:
    """
    Busca todos os produtos na FakeStore API (GET /products).

    Função reutilizável — mesma lógica da task buscar_produtos do DAG.
    Erros HTTP disparam exceção para retry do Airflow.
    """
    import requests

    log.info("Consultando FakeStore API: %s", FAKESTORE_PRODUCTS_URL)

    response = requests.get(FAKESTORE_PRODUCTS_URL, timeout=API_REQUEST_TIMEOUT)
    response.raise_for_status()

    produtos_brutos = response.json()

    if not isinstance(produtos_brutos, list) or len(produtos_brutos) == 0:
        raise ValueError("FakeStore API retornou catálogo vazio ou formato inválido")

    produtos: list[ProdutoResumo] = [
        ProdutoResumo(
            id=int(produto["id"]),
            price=float(produto["price"]),
            category=str(produto["category"]),
        )
        for produto in produtos_brutos
    ]

    log.info("✓ Ingestão concluída — %d produtos", len(produtos))
    return produtos
