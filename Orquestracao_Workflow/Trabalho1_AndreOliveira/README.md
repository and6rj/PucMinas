# Trabalho 1 — ShopBrasil Panorama de Preços

**Disciplina:** Orquestração de Workflow  
**Atividade:** 01 — Apache Airflow  
**Autor:** André Cardoso de Oliveira

Pipeline de dados no Apache Airflow que substitui o script cron da ShopBrasil: coleta produtos da [FakeStore API](https://fakestoreapi.com/docs), calcula métricas de preço por categoria e persiste o resultado no PostgreSQL analítico.

> Enunciado completo da atividade: [docs/enunciado-atividade-01.md](docs/enunciado-atividade-01.md)

---

## Contexto e problema

A ShopBrasil é um marketplace em crescimento. Todo dia, antes do expediente, o time de pricing consulta um painel com **preço médio, mínimo, máximo e quantidade de produtos por categoria**.

A solução anterior — script Python via cron — apresentava falhas silenciosas, duplicação de dados em reprocessamento e necessidade de alterar código a cada nova categoria.

Este projeto entrega um **pipeline modular no Airflow** como referência técnica para o time de dados.

---

## Solução implementada

| Requisito | Implementação |
|-----------|---------------|
| Agendamento 06:00 (Brasília) | `CronTriggerTimetable("0 6 * * *", timezone=America/Sao_Paulo)` |
| Timezone + `catchup=False` | `pendulum.timezone("America/Sao_Paulo")`, `start_date=2024-01-01`, `catchup=False` |
| TaskFlow API | `@dag` / `@task` / `@task_group` em `dags/shopbrasil_panorama_precos.py` |
| XCom automático | Retorno das tasks injetado nos argumentos downstream |
| Topologia linear | `ingestao`: buscar → validar → listar categorias |
| Fan-out | `calcular_metricas.partial(...).expand(categoria=...)` |
| Fan-in | Task `consolidar` reúne métricas das mapped tasks |
| Retries + backoff | `retries=3`, `retry_exponential_backoff=True` (2 → 4 → 8 min) |
| try/except + raise | Task `buscar_produtos` trata erros HTTP e de parsing |
| Callbacks | `on_success`, `on_failure`, `on_retry` em `buscar_produtos` |
| Dynamic Task Mapping | Uma task por categoria descoberta em runtime |
| Pool (2 slots) | `pool=ecommerce_pool` (criado no `airflow-init`) |
| 2 TaskGroups | `ingestao` e `analise` |
| PostgresHook + Connection | Connection `postgres_lab` → banco `labdb` |
| Carga idempotente | `DELETE` por `data_referencia` + `INSERT` (constraint `UNIQUE`) |
| Alertas em falha | Callbacks registram em `etl_log` + logs estruturados |

---

## Arquitetura do pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  DAG: shopbrasil_panorama_precos  (06:00 America/Sao_Paulo)     │
├─────────────────────────────────────────────────────────────────┤
│  TaskGroup: ingestao (linear)                                   │
│    buscar_produtos ──► validar_produtos ──► listar_categorias   │
│         │ callbacks + retry/backoff                             │
├─────────────────────────────────────────────────────────────────┤
│  TaskGroup: analise                                             │
│    calcular_metricas.expand(categoria)  ◄── fan-out (pool x2) │
│              │                                                  │
│              ▼                                                  │
│         consolidar  ◄── fan-in                                  │
│              │                                                  │
│              ▼                                                  │
│           carregar ──► verificar  (PostgresHook, idempotente)   │
└─────────────────────────────────────────────────────────────────┘
         ▲                              │
         │ FakeStore API                ▼ PostgreSQL (labdb)
    /products                    precos_categoria
```

---

## Estrutura do projeto

```
Trabalho1_AndreOliveira/
├── README.md                          ← este arquivo
├── docs/
│   └── enunciado-atividade-01.md      ← enunciado da disciplina
├── docker-compose.yml                 ← Airflow + PostgreSQL
├── .env                               ← AIRFLOW_UID (permissões de logs)
├── dags/
│   └── shopbrasil_panorama_precos.py  ← DAG principal
├── plugins/
│   └── shopbrasil/                    ← lógica modular (padrão do time)
│       ├── config.py                  ← agendamento, API, pool, retries
│       ├── callbacks.py               ← on_success / on_failure / on_retry
│       ├── schemas.py                 ← contratos XCom (payloads pequenos)
│       ├── validate.py                ← validação de produtos
│       ├── categories.py              ← descoberta dinâmica de categorias
│       ├── transform.py               ← métricas e consolidação
│       └── load.py                    ← PostgresHook + carga idempotente
├── sql/
│   └── init.sql                       ← DDL: precos_categoria, etl_log, views
└── fake-api/                          ← API auxiliar (lab de retries)
```

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/)
- Portas livres: **8080** (Airflow UI), **5433** (PostgreSQL analítico), **5001** (fake-api)

---

## Como executar

### 1. Configurar permissões (primeira vez)

```bash
echo "AIRFLOW_UID=$(id -u)" > .env
```

### 2. Subir o ambiente

```bash
docker compose up -d
```

O serviço `airflow-init` roda automaticamente na primeira subida e:

- Migra o banco de metadados do Airflow
- Cria o usuário `admin` / senha `admin`
- Registra a connection `postgres_lab`
- Cria o pool `ecommerce_pool` (2 slots)
- Ajusta permissões da pasta `logs/`

### 3. Acessar a UI do Airflow

| Item | Valor |
|------|-------|
| URL | http://localhost:8080 |
| Usuário | `admin` |
| Senha | `admin` |
| DAG | `shopbrasil_panorama_precos` |

Ative a DAG (toggle) e dispare manualmente com **Trigger DAG** ou aguarde o schedule às 06:00.

### 4. Inspecionar os dados no PostgreSQL

```bash
docker exec -it airflow-lab-db psql -U lab -d labdb -c \
  "SELECT * FROM v_precos_categoria_painel ORDER BY data_referencia DESC, categoria;"
```

Conexão externa: `localhost:5433` — usuário `lab`, senha `lab123`, banco `labdb`.

---

## Comandos úteis

```bash
docker compose ps                  # status dos containers
docker compose logs -f airflow-scheduler   # logs do scheduler
docker compose restart airflow-scheduler     # recarregar DAGs
docker compose down -v             # derrubar e apagar volumes (reset total)
```

---

## Verificação dos requisitos (checklist)

Use este checklist ao demonstrar o trabalho na UI do Airflow:

- [ ] **Graph View** — TaskGroups `ingestao` e `analise` visíveis
- [ ] **Fan-out** — múltiplas instâncias de `analise.calcular_metricas` (uma por categoria)
- [ ] **Fan-in** — `analise.consolidar` recebe todas as mapped tasks
- [ ] **Gantt** — pool `ecommerce_pool` limitando paralelismo a 2 tasks
- [ ] **XCom** — Admin → XComs: payloads pequenos entre tasks
- [ ] **Logs** — callbacks `SHOPBRASIL ✓/✗/↻` na task `ingestao.buscar_produtos`
- [ ] **Retries** — simular falha na API e observar backoff nos logs
- [ ] **Idempotência** — re-executar a mesma run: contagem em `precos_categoria` não duplica
- [ ] **PostgreSQL** — view `v_precos_categoria_painel` com métricas do dia

---

## Tabela de destino

```sql
precos_categoria (
    data_referencia  DATE,
    categoria        VARCHAR(100),
    preco_medio      NUMERIC(10,2),
    preco_min        NUMERIC(10,2),
    preco_max        NUMERIC(10,2),
    qtd_produtos     INTEGER,
    dag_run_id       VARCHAR(250),
    UNIQUE (data_referencia, categoria)
)
```

Eventos operacionais (sucesso, falha, retry) são registrados em `etl_log`.

---

## Referências

- [FakeStore API — Swagger](https://fakestoreapi.com/docs)
- [Apache Airflow — TaskFlow API](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/taskflow.html)
- [Dynamic Task Mapping](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html)
- Enunciado da atividade: [docs/enunciado-atividade-01.md](docs/enunciado-atividade-01.md)
