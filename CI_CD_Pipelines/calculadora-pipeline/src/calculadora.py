def calcular_desconto(preco: float, percentual: float) -> float:
    if percentual < 0 or percentual > 100:
        raise ValueError("Percentual deve estar entre 0 e 100")
    return round(preco * (1 - percentual / 100), 2)


def calcular_imposto(preco: float, aliquota: float) -> float:
    if aliquota < 0:
        raise ValueError("Alíquota não pode ser negativa")
    return round(preco * (aliquota / 100), 2)


def calcular_preco_final(
    preco_base: float, desconto: float, aliquota_imposto: float
) -> float:
    preco_com_desconto = calcular_desconto(preco_base, desconto)
    imposto = calcular_imposto(preco_com_desconto, aliquota_imposto)
    return round(preco_com_desconto + imposto, 2)
