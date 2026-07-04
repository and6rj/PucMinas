"""
DAG de demonstração para Airflow + CeleryExecutor.

Objetivo:
- Mostrar distribuição automática das tarefas entre workers.
- Facilitar a visualização no Flower.
- Facilitar a análise dos logs.

Execute a DAG manualmente pela interface do Airflow.
"""

from datetime import datetime

from airflow import DAG
from airflow.decorators import task


# ------------------------------------------------------------------
# Configuração da DAG
# ------------------------------------------------------------------
with DAG(
    dag_id="example_distributed_celery_random_sleep",
    start_date=datetime(2025, 1, 1),
    schedule=None,  # somente execução manual
    catchup=False,
    tags=["aula", "celery", "distribuido"],
) as dag:

    # --------------------------------------------------------------
    # Tarefa executada pelos workers
    # --------------------------------------------------------------
    @task
    def tarefa(numero: int):
        """
        Simula um processamento qualquer.

        Cada tarefa:
        - identifica o hostname do worker
        - escolhe um tempo aleatório
        - dorme por esse tempo
        - registra tudo nos logs
        """

        import random
        import socket
        import time
        from datetime import datetime

        # Nome do container/máquina que executou a task
        worker = socket.gethostname()

        # Tempo aleatório para simular carga diferente
        tempo = random.randint(10, 30)

        print("\n" + "=" * 60)
        print(f"INÍCIO DA TASK {numero}")
        print(f"Worker........: {worker}")
        print(f"Horário.......: {datetime.now()}")
        print(f"Duração.......: {tempo} segundos")
        print("=" * 60 + "\n")

        # Simula processamento
        time.sleep(tempo)

        print("\n" + "-" * 60)
        print(f"FIM DA TASK {numero}")
        print(f"Worker........: {worker}")
        print(f"Horário.......: {datetime.now()}")
        print("-" * 60 + "\n")

        return {
            "task": numero,
            "worker": worker,
            "duracao": tempo,
        }

    # --------------------------------------------------------------
    # Criação das tarefas paralelas
    # --------------------------------------------------------------
    #
    # Como não existe dependência entre elas,
    # o Celery pode distribuí-las livremente
    # entre os workers disponíveis.
    #
    for i in range(1, 21):
        tarefa.override(
            task_id=f"tarefa_{i:02d}"
        )(i)