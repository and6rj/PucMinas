"""Avaliação: o fato certo aparece, sources cita o documento, a AURA fica no banco."""

import pytest

from aura_testes import (
    carregar_golden,
    eh_infra,
    fatos_faltando,
    fontes_faltando,
    indica_indisponivel,
    itens_da_categoria,
    mensagem_falha,
)

_GOLDEN = carregar_golden()
_ITENS = itens_da_categoria(_GOLDEN, "avaliacao")


def _exigir_gravacao(item):
    gravada = item.get("resposta_gravada") or {}
    assert gravada.get("message"), mensagem_falha(
        item, "resposta ainda não gravada; rode o passo de gravação"
    )
    assert not eh_infra(gravada["message"]), mensagem_falha(
        item, "a gravação é erro de infraestrutura, não resposta da AURA"
    )


@pytest.mark.parametrize("item", _ITENS, ids=lambda item: item["id"])
def test_fato_certo_aparece(item, registrar):
    registrar(item)
    _exigir_gravacao(item)
    texto = item["resposta_gravada"]["message"]
    faltando = fatos_faltando(texto, item["fatos"])
    assert not faltando, mensagem_falha(item, f"fatos ausentes: {faltando}")


@pytest.mark.parametrize("item", _ITENS, ids=lambda item: item["id"])
def test_sources_cita_o_documento(item, registrar):
    registrar(item)
    _exigir_gravacao(item)
    faltando = fontes_faltando(
        item["resposta_gravada"].get("sources"), item["sources_esperadas"]
    )
    assert not faltando, mensagem_falha(item, f"sources sem o documento: {faltando}")


@pytest.mark.parametrize("item", _ITENS, ids=lambda item: item["id"])
def test_resposta_fica_no_escopo_do_banco(item, registrar):
    registrar(item)
    _exigir_gravacao(item)
    texto = item["resposta_gravada"]["message"]
    assert not indica_indisponivel(texto), mensagem_falha(
        item, "a pergunta está nos documentos, mas a AURA tratou como fora de escopo"
    )
