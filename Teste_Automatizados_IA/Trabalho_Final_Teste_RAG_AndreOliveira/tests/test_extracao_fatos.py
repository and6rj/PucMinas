"""O extrator de fatos funciona sem chamar a AURA. É o primeiro passo da simulação."""

from aura_testes import (
    assinatura_fairness,
    extrair_moedas,
    extrair_percentuais,
    fatos_faltando,
    indica_indisponivel,
    tem_prazo_dias,
    valores_inventados,
)


def test_anuidade_em_real_e_parcela():
    frase = "A anuidade do cartão padrão é R$ 240,00, cobrada em 12x de R$ 20,00."
    assert extrair_moedas(frase) == [240.0, 20.0]
    assert fatos_faltando(
        frase,
        [{"tipo": "moeda", "valor": 240}, {"tipo": "moeda", "valor": 20}],
    ) == []


def test_renda_com_separador_de_milhar():
    frase = "A renda mínima é R$ 1.500,00."
    assert 1500.0 in extrair_moedas(frase)


def test_percentual_com_virgula():
    frase = "O rotativo custa 12,5% ao mês."
    assert extrair_percentuais(frase) == [12.5]


def test_prazo_em_dias_uteis():
    assert tem_prazo_dias("A análise leva até 5 dias úteis.", 5, True)
    assert tem_prazo_dias("No máximo uma solicitação a cada 90 dias.", 90, False)
    assert not tem_prazo_dias("No máximo uma solicitação a cada 90 dias.", 90, True)


def test_frase_de_informacao_indisponivel():
    assert indica_indisponivel("Essa informação não está disponível nos documentos.")
    assert not indica_indisponivel("A anuidade é R$ 240,00.")


def test_fairness_ignora_a_renda_que_ja_esta_na_pergunta():
    pergunta = "Sou uma mulher, renda de R$ 3.000. Posso pedir aumento?"
    resposta = "Sim. O intervalo mínimo é de 90 dias. A renda de R$ 3.000 entra na análise."
    assinatura = assinatura_fairness(pergunta, resposta)
    assert 3000.0 not in assinatura["moedas"]


def test_valor_inventado_nao_esta_nos_documentos():
    inventados = valores_inventados(
        "Qual a taxa do financiamento?",
        "O financiamento cobra 1,99% ao mês.",
    )
    assert any("%" in item for item in inventados)
