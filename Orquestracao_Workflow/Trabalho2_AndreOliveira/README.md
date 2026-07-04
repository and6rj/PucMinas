# Trabalho 2 — ShopBrasil com CeleryExecutor

**Disciplina:** Orquestração de Workflow  
**Atividade:** 02 — Airflow distribuído (Scheduler + Workers)  
**Autor:** André Cardoso de Oliveira

Evolução do [Trabalho 1](Trabalho1_AndreOliveira/README.md): o mesmo pipeline ShopBrasil (FakeStore API → métricas por categoria → PostgreSQL) passa a rodar em arquitetura **distribuída** com **CeleryExecutor**.

O scheduler **não executa** as tasks. Ele as enfileira no Redis; os **workers** consomem a fila e executam o código.

---

## Arquitetura

```
┌──────────────────────────── airflow-scheduler/ ─────────────────────────────┐
│  Webserver (:8080)   Scheduler   Triggerer   Flower (:5555)                 │
│  Postgres meta       Redis (broker)   Redis Commander (:8081)               │
│  Postgres lab (:5433) — destino ETL (precos_categoria)                      │
│  DAGs + plugins ShopBrasil                                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ fila Redis (default)
                                    ▼
┌──────────────────────────── airflow-workers/ ───────────────────────────────┐
│  worker-1   worker-2   (ou N workers via --scale)                           │
│  Montam dags/logs/plugins do scheduler                                      │
│  Executam tasks e gravam no postgres-lab                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Pasta | Responsabilidade |
|-------|------------------|
| `airflow-scheduler/` | Controle: metadados, broker, UI, Flower, banco analítico, DAGs |
| `airflow-workers/` | Execução: workers Celery que processam as tasks |
| `Trabalho1_AndreOliveira/` | Referência do lab anterior (LocalExecutor, monólito) |

---

## Pré-requisitos

- Docker e Docker Compose
- Portas livres: **8080**, **5555**, **8081**, **5432**, **5433**, **6379**, **5001**

---

## Como executar

### 1. Subir o scheduler (Máquina 1)

```bash
cd airflow-scheduler
docker compose -f docker-compose-scheduler.yaml up -d
```

Aguarde o `airflow-init` concluir (usuário, connection `postgres_lab`, pool `ecommerce_pool`).

### 2. Subir os workers (Máquina 2 — aqui, mesma máquina)

**Opção A — 2 workers fixos:**

```bash
cd ../airflow-workers
docker compose -f docker-compose-workers.yaml up -d
```

**Opção B — workers dinâmicos (escala horizontal):**

```bash
cd ../airflow-workers
docker compose -f docker-compose-workers-dynamic.yaml up -d --scale airflow-worker=3
```

### 3. Acessar as UIs

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | `airflow` / `airflow` |
| Flower | http://localhost:5555 | — |
| Redis Commander | http://localhost:8081 | — |

### 4. Rodar o pipeline ShopBrasil

1. Ative a DAG `shopbrasil_panorama_precos`
2. **Trigger DAG**
3. No **Flower**, observe workers ativos e tasks em execução
4. Nos **logs** de cada task, procure `worker=<hostname>` — hostnames diferentes confirmam distribuição
5. No fan-out (`calcular_metricas`), o pool `ecommerce_pool` limita a **2** tasks paralelas (visível no Gantt)

### 5. Inspecionar o PostgreSQL analítico

```bash
docker exec -it airflow-lab-db psql -U lab -d labdb -c \
  "SELECT * FROM v_precos_categoria_painel ORDER BY data_referencia DESC, categoria;"
```

Conexão externa: `localhost:5433` — usuário `lab`, senha `lab123`, banco `labdb`.

---

## O que mudou em relação ao Trabalho 1

| Aspecto | Trabalho 1 | Trabalho 2 |
|---------|------------|------------|
| Executor | `LocalExecutor` | `CeleryExecutor` |
| Onde a task roda | No mesmo stack do scheduler | Em containers **workers** |
| Broker | — | **Redis** |
| Monitoramento workers | — | **Flower** |
| Escala | Vertical (um processo) | Horizontal (`--scale`) |
| Pipeline de negócio | ShopBrasil | **Mesmo** ShopBrasil |

A lógica de ingestão, validação, métricas, carga idempotente e callbacks permanece a do Trabalho 1. O que muda é **quem executa** as tasks.

---

## DAGs disponíveis

| DAG | Origem |
|-----|--------|
| `shopbrasil_panorama_precos` | Pipeline principal (Trabalho 1 adaptado) |
| `example_distributed_celery*` | Exemplos da aula (em `dags/exemplos/`) |

---

## Comandos úteis

```bash
# Status
docker compose -f airflow-scheduler/docker-compose-scheduler.yaml ps
docker compose -f airflow-workers/docker-compose-workers.yaml ps

# Logs
docker compose -f airflow-scheduler/docker-compose-scheduler.yaml logs -f airflow-scheduler
docker logs -f airflow-worker-1

# Escalar workers (versão dinâmica)
cd airflow-workers
docker compose -f docker-compose-workers-dynamic.yaml up -d --scale airflow-worker=4

# Derrubar tudo
cd airflow-workers && docker compose -f docker-compose-workers.yaml down
cd ../airflow-scheduler && docker compose -f docker-compose-scheduler.yaml down
```

---

## Checklist de demonstração

- [ ] Flower mostra 2+ workers online
- [ ] Trigger da DAG `shopbrasil_panorama_precos` completa com sucesso
- [ ] Logs exibem `worker=` com hostnames distintos entre tasks
- [ ] Fan-out de `calcular_metricas` respeita pool de 2 slots (Gantt)
- [ ] Tabela `precos_categoria` populada; re-run não duplica (idempotência)
- [ ] Escalando workers (`--scale`), o Flower reflete a nova quantidade
