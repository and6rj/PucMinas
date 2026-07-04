"""
DAG para demonstrar execução distribuída com CeleryExecutor.

Objetivos:
1. Criar várias tarefas independentes.
2. Permitir que o Celery distribua as tarefas entre os workers.
3. Mostrar nos logs qual worker executou cada tarefa.
"""

from datetime import datetime
from airflow import DAG
from airflow.decorators import task

# Configuração básica da DAG
with DAG(
    dag_id="example_distributed_celery_fixed_sleep",
    start_date=datetime(2025, 1, 1),
    schedule=None,          # Executa apenas manualmente
    catchup=False,
    tags=["aula", "celery", "distribuido"],
) as dag:

    @task
    def tarefa(numero):
        """
        Tarefa simples para demonstrar distribuição.

        Cada execução:
        - identifica o hostname do worker
        - espera alguns segundos
        - retorna informações para os logs
        """

        import socket
        import time
        from datetime import datetime

        hostname = socket.gethostname()

        print("=" * 50)
        print(f"Tarefa: {numero}")
        print(f"Worker: {hostname}")
        print(f"Início: {datetime.now()}")
        print("=" * 50)

        # Simula processamento
        time.sleep(20)

        print(f"Tarefa {numero} finalizada em {hostname}")

        return {
            "tarefa": numero,
            "worker": hostname,
        }

    # Cria 10 tarefas independentes
    #
    # Como não existe dependência entre elas,
    # o Celery pode distribuí-las livremente
    # entre os workers disponíveis.
    for i in range(1, 11):
        tarefa.override(task_id=f"tarefa_{i}")(i)