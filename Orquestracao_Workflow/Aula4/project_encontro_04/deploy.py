from prefect import flow

if __name__ == "__main__":
    # Declaração do arquivo a ser deployado
    flow.from_source(
        source=".",                               # código local, mesma máquina do worker
        entrypoint="example_1.py:meu_pipeline",
    ).deploy(
        name="exemplo-local",
        work_pool_name="aula-04",
        cron="0 20 * * *",        # todo dia às 20:00
    )
    # Exemplo 2 — Block com API key (OpenWeatherMap)
    flow.from_source(
        source=".",
        entrypoint="example_2_block.py:pipeline_clima",
    ).deploy(
        name="exemplo-clima_api_key",
        work_pool_name="aula-04",
        cron="0 22 * * *", # todo dia às 22:00
    )
    # Exemplo 3 — Block com usuário e senha (Fake Store API)
    flow.from_source(
        source=".",
        entrypoint="example_3_block.py:pipeline_auth",
    ).deploy(
        name="exemplo-fake_api_user_pass",
        work_pool_name="aula-04",
        cron="0 21 * * *", # todo dia às 21:00
    )
    # Exemplo 4 — .map() fan-out e fan-in
    flow.from_source(
        source=".",
        entrypoint="example_4_map.py:pipeline_precos",
    ).deploy(
        name="exemplo-fake_api_map_fan-out_fan-in",
        work_pool_name="aula-04",
        cron="0 7 * * *", # todo dia às 07:00
    )
    # Exemplo 5a — Automation: flow de ingestão (dispara a Automation)
    flow.from_source(
        source=".",
        entrypoint="example_5_automation_part_1.py:ingestao_produtos"
    ).deploy(
        name="exemplo-automacao-ingestao",
        work_pool_name="aula-04",
        cron="0 7 * * *", # todo dia às 07:00
    )
    # Exemplo 5b — Automation: flow de relatório (disparado pela Automation)
    flow.from_source(
        source=".",
        entrypoint="example_5_automation_part_2.py:gerar_relatorio"
    ).deploy(
        name="exemplo-automacao-relatorio",
        work_pool_name="aula-04",
        cron="0 7 * * *", # todo dia às 07:00
    )