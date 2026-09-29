"""Grava cada pergunta uma vez. A suíte do dia a dia não chama a API."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aura_testes import CotaEsgotada, gravar_respostas


def main() -> int:
    parser = argparse.ArgumentParser(description="Grava as respostas da AURA no golden dataset")
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Pergunta de novo mesmo que já exista resposta gravada",
    )
    args = parser.parse_args()
    try:
        gravar_respostas(atualizar=args.atualizar)
    except CotaEsgotada as erro:
        print(f"COTA_ESGOTADA: {erro}", flush=True)
        print("O que já foi gravado permanece em golden/golden_dataset.json.", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
