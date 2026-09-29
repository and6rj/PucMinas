"""Escreve relatorio/falhas.md com teste, pergunta, resposta e data."""

from datetime import datetime
from pathlib import Path

import pytest

FALHAS = []
RAIZ = Path(__file__).resolve().parents[1]


def _propriedade(item, nome: str) -> str:
    encontrado = ""
    for chave, valor in item.user_properties:
        if chave == nome:
            encontrado = valor
    return encontrado


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    relatorio = resultado.get_result()
    if relatorio.when != "call" or relatorio.passed or relatorio.skipped:
        return
    FALHAS.append(
        {
            "teste": item.nodeid,
            "pergunta": _propriedade(item, "pergunta"),
            "resposta": _propriedade(item, "resposta"),
            "data": _propriedade(item, "data"),
            "detalhe": str(relatorio.longrepr),
        }
    )


def pytest_sessionfinish(session, exitstatus):
    hoje = datetime.now().astimezone().isoformat(timespec="seconds")
    linhas = [
        "# Falhas encontradas",
        "",
        f"Data da execução: {hoje}",
        "",
        "A suíte normal compara fatos com as respostas gravadas em `golden/golden_dataset.json`.",
        "Ela não chama a API. Texto diferente com o mesmo fato não é falha.",
        "",
    ]
    if not FALHAS:
        linhas.append("Nenhuma falha nesta execução.")
    else:
        for indice, falha in enumerate(FALHAS, start=1):
            linhas.extend(
                [
                    f"## {indice}. `{falha['teste']}`",
                    "",
                    f"- Data da resposta: {falha['data'] or 'não informada'}",
                    f"- Pergunta: {falha['pergunta'] or 'ver detalhe abaixo'}",
                    "",
                    "Resposta recebida:",
                    "",
                    "```",
                    falha["resposta"] or "(vazia — ver detalhe)",
                    "```",
                    "",
                    "Detalhe do pytest:",
                    "",
                    "```",
                    falha["detalhe"],
                    "```",
                    "",
                ]
            )
    destino = RAIZ / "relatorio" / "falhas.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    if exitstatus != 0 and not FALHAS:
        return


@pytest.fixture
def registrar(request):
    def _registrar(item: dict) -> None:
        gravada = item.get("resposta_gravada") or {}
        request.node.user_properties.append(("pergunta", item.get("pergunta", "")))
        request.node.user_properties.append(("resposta", gravada.get("message", "")))
        request.node.user_properties.append(("data", gravada.get("coletado_em", "")))

    return _registrar
