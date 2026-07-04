"""
DAG de exemplo para demonstrar execução distribuída com CeleryExecutor.

Estrutura:
  start → [task_a, task_b, task_c, task_d] → end

As 4 tasks intermediárias rodam em paralelo e são distribuídas
entre os workers disponíveis. Cada task imprime em qual worker
(hostname do container) foi executada.
"""

import socket
import time
from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="example_distributed_celery",
    description="Demonstra distribuição de tasks entre workers Celery",
    schedule=None,          # execução manual
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["exemplo", "distribuido", "celery"],
)
def example_distributed():

    @task
    def start():
        hostname = socket.gethostname()
        print(f"[START] Iniciando pipeline no worker: {hostname}")
        return {"status": "started", "worker": hostname}

    @task
    def task_a():
        hostname = socket.gethostname()
        print(f"[TASK_A] Executando no worker: {hostname}")
        time.sleep(3)
        print(f"[TASK_A] Concluída no worker: {hostname}")
        return hostname

    @task
    def task_b():
        hostname = socket.gethostname()
        print(f"[TASK_B] Executando no worker: {hostname}")
        time.sleep(3)
        print(f"[TASK_B] Concluída no worker: {hostname}")
        return hostname

    @task
    def task_c():
        hostname = socket.gethostname()
        print(f"[TASK_C] Executando no worker: {hostname}")
        time.sleep(3)
        print(f"[TASK_C] Concluída no worker: {hostname}")
        return hostname

    @task
    def task_d():
        hostname = socket.gethostname()
        print(f"[TASK_D] Executando no worker: {hostname}")
        time.sleep(3)
        print(f"[TASK_D] Concluída no worker: {hostname}")
        return hostname

    @task
    def end(workers: list):
        print("[END] Pipeline concluído.")
        print("[END] Tasks executadas nos workers:")
        for i, w in enumerate(workers, start=1):
            print(f"  task_{chr(64+i)} → {w}")

        unique_workers = set(workers)
        if len(unique_workers) > 1:
            print(f"[END] Distribuição confirmada: {len(unique_workers)} workers distintos usados.")
        else:
            print("[END] Todas as tasks rodaram no mesmo worker (apenas 1 worker disponível).")

    # Grafo de dependências
    inicio = start()
    a = task_a()
    b = task_b()
    c = task_c()
    d = task_d()

    # start precisa rodar antes das tasks paralelas
    inicio >> [a, b, c, d]

    # end recebe os resultados das 4 tasks
    end([a, b, c, d])


example_distributed()
