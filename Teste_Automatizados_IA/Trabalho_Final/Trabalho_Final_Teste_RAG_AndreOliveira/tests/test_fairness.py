"""Fairness: a mesma pergunta, trocando só um atributo sensível, gera os mesmos fatos."""

import pytest

from aura_testes import (
    assinatura_fairness,
    carregar_golden,
    eh_infra,
    fatos_faltando,
    fontes_faltando,
    item_por_id,
    mensagem_falha,
)

_GOLDEN = carregar_golden()
_PARES = _GOLDEN["pares_fairness"]


def _lado(par, chave):
    item = item_por_id(_GOLDEN, par[chave])
    gravada = item.get("resposta_gravada") or {}
    assert gravada.get("message"), mensagem_falha(item, "resposta ainda não gravada")
    assert not eh_infra(gravada["message"]), mensagem_falha(
        item, "gravação é erro de infraestrutura"
    )
    return item


@pytest.mark.parametrize("par", _PARES, ids=lambda par: par["id"])
def test_fatos_extraidos_sao_iguais(par, registrar):
    lado_a = _lado(par, "id_a")
    lado_b = _lado(par, "id_b")
    registrar(lado_a)
    assinatura_a = assinatura_fairness(lado_a["pergunta"], lado_a["resposta_gravada"]["message"])
    assinatura_b = assinatura_fairness(lado_b["pergunta"], lado_b["resposta_gravada"]["message"])
    assert assinatura_a == assinatura_b, (
        f"Teste: {par['id']}\n"
        f"Atributo: {par['atributo']}\n"
        f"Pergunta A: {lado_a['pergunta']}\n"
        f"Resposta A: {lado_a['resposta_gravada']['message']}\n"
        f"Data A: {lado_a['resposta_gravada'].get('coletado_em')}\n"
        f"Pergunta B: {lado_b['pergunta']}\n"
        f"Resposta B: {lado_b['resposta_gravada']['message']}\n"
        f"Data B: {lado_b['resposta_gravada'].get('coletado_em')}\n"
        f"Fatos A: {assinatura_a}\n"
        f"Fatos B: {assinatura_b}"
    )


@pytest.mark.parametrize("par", _PARES, ids=lambda par: par["id"])
def test_os_dois_lados_tem_o_fato_da_politica(par, registrar):
    for chave in ("id_a", "id_b"):
        item = _lado(par, chave)
        registrar(item)
        faltando = fatos_faltando(item["resposta_gravada"]["message"], par["fatos"])
        assert not faltando, mensagem_falha(item, f"fatos ausentes: {faltando}")


@pytest.mark.parametrize("par", _PARES, ids=lambda par: par["id"])
def test_os_dois_lados_citam_o_documento_da_politica(par, registrar):
    for chave in ("id_a", "id_b"):
        item = _lado(par, chave)
        registrar(item)
        faltando = fontes_faltando(
            item["resposta_gravada"].get("sources"), item["sources_esperadas"]
        )
        assert not faltando, mensagem_falha(item, f"sources sem o documento: {faltando}")
