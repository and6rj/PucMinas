"""
Contratos de dados trafegados entre tasks via XCom.

TaskFlow API persiste automaticamente o return de cada @task no XCom.
Regra do time: passar apenas payloads pequenos (tipos nativos JSON-serializáveis).

Fluxo de XCom neste pipeline:
  buscar_produtos      → list[ProdutoResumo]
  validar_produtos     → list[ProdutoResumo]
  listar_categorias    → list[str]              (fan-out trigger)
  calcular_metricas[*] → MetricaCategoria      (1 dict por categoria mapeada)
  consolidar           → list[MetricaCategoria] (fan-in collect)
  carregar             → int
  verificar            → None
"""

from typing import TypedDict


class ProdutoResumo(TypedDict):
    """Subset enxuto do produto FakeStore — suficiente para agregação."""

    id: int
    price: float
    category: str


class MetricaCategoria(TypedDict):
    """Métricas diárias por categoria — payload mínimo para carga no banco."""

    categoria: str
    preco_medio: float
    preco_min: float
    preco_max: float
    qtd_produtos: int
