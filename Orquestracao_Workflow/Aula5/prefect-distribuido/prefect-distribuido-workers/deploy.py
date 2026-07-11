"""
deploy.py — registra o deployment do flow no work pool "lab-pool".

Rodado DENTRO da imagem do worker (ver README), para que o caminho do código
(/opt/prefect) seja exatamente o mesmo que os workers enxergam em runtime.

from_source(source=<dir local na imagem>) faz o worker carregar o código desse
caminho na hora de executar. Como deploy e workers usam a MESMA imagem, os
caminhos batem.

Variante de produção (código fora da imagem): troque o source por um repositório
Git, e a imagem do worker carrega só Python + dependências:

    flow.from_source(
        source="https://github.com/seu-usuario/seu-repo.git",
        entrypoint="flows/clima.py:analise_clima_multiplas_cidades",
    ).deploy(...)
"""

from pathlib import Path

from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source=str(Path(__file__).parent),
        entrypoint="flows/clima.py:analise_clima_multiplas_cidades",
    ).deploy(
        name="clima-distribuido",
        work_pool_name="lab-pool",
        cron="*/5 * * * *",  # a cada 5 min, para ver a distribuição rápido
        tags=["aula3", "distribuido"],
    )
    print("Deployment 'analise-clima/clima-distribuido' registrado no pool 'lab-pool'.")
