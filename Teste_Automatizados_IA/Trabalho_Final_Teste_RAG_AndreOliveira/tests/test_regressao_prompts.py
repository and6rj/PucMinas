"""Regressão de prompts: o golden dataset versionado é a referência.

A suíte normal olha a gravação. A marcação live pergunta de novo ao sistema no ar
e só cobra os fatos, não a frase.
"""

import pytest

from aura_testes import (
    VERSAO_GOLDEN,
    carregar_credenciais,
    carregar_golden,
    eh_infra,
    fatos_faltando,
    ids_obrigatorios,
    mensagem_falha,
)

_GOLDEN = carregar_golden()


def test_golden_esta_versionado():
    assert _GOLDEN["versao"] == VERSAO_GOLDEN
    assert _GOLDEN.get("coletado_em"), "o golden ainda não tem data de coleta"
    assert _GOLDEN["itens"], "o golden está vazio"
    assert _GOLDEN["pares_fairness"], "o golden não tem pares de fairness"


def test_perguntas_e_fatos_continuam_os_do_catalogo():
    ids = [item["id"] for item in _GOLDEN["itens"]]
    assert ids == ids_obrigatorios()
    for item in _GOLDEN["itens"]:
        assert item["pergunta"].strip()
        assert item["fatos"]
        gravada = item.get("resposta_gravada") or {}
        assert gravada.get("message"), mensagem_falha(item, "falta resposta gravada")
        assert gravada.get("coletado_em"), mensagem_falha(item, "falta data da coleta")
        assert not eh_infra(gravada["message"]), mensagem_falha(
            item, "gravação é erro de infraestrutura"
        )


@pytest.fixture(scope="session")
def cliente_live():
    try:
        from aura_testes import AuraClient

        usuario, senha = carregar_credenciais()
    except RuntimeError as erro:
        pytest.skip(str(erro))
    cliente = AuraClient(usuario, senha)
    cliente.login()
    return cliente


@pytest.mark.live
@pytest.mark.parametrize("item", _GOLDEN["itens"], ids=lambda item: item["id"])
def test_sistema_no_ar_mantem_os_fatos(item, registrar, cliente_live):
    registrar(item)
    atual = cliente_live.perguntar(item["pergunta"])
    item_vivo = {
        **item,
        "resposta_gravada": {
            "message": atual.get("message", ""),
            "sources": atual.get("sources", []),
            "coletado_em": (item.get("resposta_gravada") or {}).get("coletado_em", ""),
        },
    }
    registrar(item_vivo)
    assert not eh_infra(atual.get("message", "")), mensagem_falha(
        item_vivo, "resposta ao vivo é erro de infraestrutura"
    )
    faltando = fatos_faltando(atual.get("message", ""), item["fatos"])
    assert not faltando, mensagem_falha(item_vivo, f"regressão de fatos: {faltando}")
