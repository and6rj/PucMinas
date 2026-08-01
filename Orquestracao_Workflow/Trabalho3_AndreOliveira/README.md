# Trabalho 3 — Monitoramento de Inflação de Alimentos Básicos (IPCA)

**Instituição de Ensino:** PUC Minas  
**Curso:** Engenharia de IA  
**Disciplina:** Orquestração de Workflow  
**Professor:** Reinaldo Carlos Mendes  
**Projeto Final:** Pipeline ETL + ML com Apache Airflow distribuído  
**Autor:** André Cardoso de Oliveira  
**Repositório:** [GitHub](https://github.com/and6rj/PucMinas/tree/main/Orquestracao_Workflow/Trabalho3_AndreOliveira)

Pipeline de dados que monitora a inflação de alimentos básicos no Brasil, consumindo a **API oficial do IBGE (SIDRA — Tabela 7060, IPCA)**, aplicando transformações em camadas, treinando modelos de previsão com **scikit-learn**, rastreando experimentos no **MLflow** e persistindo resultados em **PostgreSQL**. Toda a stack roda localmente via `docker compose up`.

---

## Problema e contexto

A inflação de alimentos básicos impacta diretamente o orçamento familiar e decisões de política econômica. Acompanhar a variação mensal de itens como arroz, feijão, leite e carnes exige:

- coleta periódica de séries históricas confiáveis;
- tratamento e padronização dos dados brutos;
- modelagem preditiva para antecipar tendências;
- rastreabilidade dos experimentos de ML e reprodutibilidade das execuções.

Este projeto automatiza esse fluxo ponta a ponta com orquestração distribuída: o **Airflow** coordena ETL e etapas de ML; o **MLflow** registra métricas, parâmetros e modelos; o **PostgreSQL** concentra metadados, tracking e dados analíticos.

**Fonte de dados:** [SIDRA/IBGE — Tabela 7060 (IPCA)](https://apisidra.ibge.gov.br/)

---

## Arquitetura da solução

```
┌─────────────────────────────────── Docker Compose ───────────────────────────────────┐
│                                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────────────────┐  │
│  │  PostgreSQL │    │    Redis    │    │  MLflow Server (:5000)                   │  │
│  │  (:5432)    │    │  (broker)   │    │  backend: DB mlflow | artifacts: volume  │  │
│  │             │    │             │    └──────────────────────────────────────────┘  │
│  │  DB airflow │    └──────┬──────┘                      ▲                           │
│  │  DB mlflow  │           │ fila Celery                  │ MLFLOW_TRACKING_URI       │
│  │  DB ipca    │           ▼                              │                           │
│  │  (Bronze/   │    ┌─────────────────────────────────────────────────────────────┐  │
│  │   Silver/   │    │  Airflow (CeleryExecutor)                                   │  │
│  │   Gold)     │    │  Init │ Webserver (:8080) │ Scheduler │ Flower (:5555)      │  │
│  └──────▲──────┘    └───────────────────────────┬─────────────────────────────────┘  │
│         │                                      │                                     │
│         │ persistência                         │ 3× airflow-worker (réplicas Celery)  │
│         │                                      ▼                                     │
│  ┌──────┴──────────────────────────────────────────────────────────────────────────┐  │
│  │  DAG: inflacao_alimentos_mlops (dags/)                                        │  │
│  │                                                                               │  │
│  │  Fase 1 Fan-out : extrair_alimento.expand → persistir_raw.expand              │  │
│  │  Fase 2 Linear  : treinar_modelo (MLflow)                                   │  │
│  │  Fase 3 Fan-in  : consolidar_alerta → gold.tb_alerta_inflacao                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘
         ▲
         │ HTTPS
    IBGE SIDRA API (Tabela 7060 — IPCA)
```

### Camadas de dados (Medallion)

| Camada | Schema | Responsabilidade |
|--------|--------|------------------|
| **Bronze** | `bronze` | Ingestão bruta da API SIDRA (`raw_ipca`) com payload JSON |
| **Silver** | `silver` | Limpeza, tipagem, deduplicação e séries temporais padronizadas |
| **Gold** | `gold` | Métricas finais, predições e painel analítico (`predicoes_inflacao`) |

### Serviços Docker

| Serviço | Imagem / build | Porta | Função |
|---------|----------------|-------|--------|
| `postgres` | `postgres:16` | 5432 | Backend Airflow, MLflow e Target DB |
| `redis` | `redis:7.2` | 6379 | Message broker do Celery |
| `mlflow` | `python:3.11-slim` | **5000** | UI de experimentos e Model Registry |
| `airflow-init` | `trabalho3-airflow:latest` | — | Migração, usuário admin, connections |
| `airflow-webserver` | idem | **8080** | Interface do Airflow |
| `airflow-scheduler` | idem | — | Agendamento e enfileiramento de tasks |
| `airflow-worker` | idem | — | Execução distribuída (**3 réplicas**) |
| `airflow-flower` | idem | **5555** | Monitoramento dos workers Celery |

---

## Ferramentas e justificativa

| Ferramenta | Papel | Por que esta escolha |
|------------|-------|----------------------|
| **Apache Airflow** | Orquestração ETL + ML | DAGs declarativas, agendamento, retries, observabilidade via UI e logs; evolução natural dos Trabalhos 1 e 2 |
| **CeleryExecutor** | Execução distribuída | Permite paralelizar extração por produto, treino de modelos e inferência em workers independentes |
| **Redis** | Broker Celery | Leve, rápido e padrão de mercado para filas do Airflow distribuído |
| **MLflow** | Tracking de ML | Registra métricas (MAE, RMSE), hiperparâmetros, artefatos e versionamento de modelos |
| **PostgreSQL** | Persistência unificada | Um único container com databases isolados reduz complexidade local sem sacrificar separação lógica |
| **scikit-learn** | Modelagem | Regressão temporal para previsão de inflação — simples, interpretável e adequada ao escopo acadêmico |
| **Docker Compose** | Infraestrutura | Reprodutibilidade: qualquer avaliador sobe o projeto com um comando |

---

## Estrutura do projeto

```
Trabalho3_AndreOliveira/
├── README.md                 ← este arquivo
├── docker-compose.yml        ← stack completa (CeleryExecutor + MLflow)
├── Dockerfile                ← imagem Airflow customizada
├── .env                      ← AIRFLOW_UID e credenciais
├── sql/
│   └── init.sql              ← databases, schemas Bronze/Silver/Gold
├── dags/                     ← DAGs do Airflow
├── plugins/                  ← módulos reutilizáveis (API IBGE, ML, carga)
└── logs/                     ← logs de execução (gerados em runtime)
```

---

## Pré-requisitos

- Docker Engine 24+ e Docker Compose V2
- Portas livres: **5432**, **6379**, **5000**, **8080**, **5555**
- ~4 GB RAM disponíveis (recomendado para 3 workers + MLflow)

---

## Como executar (do zero)

### 1. Clonar e entrar na pasta

```bash
cd Trabalho3_AndreOliveira
```

### 2. Configurar permissões (Linux)

```bash
echo "AIRFLOW_UID=$(id -u)" > .env
echo "_AIRFLOW_WWW_USER_USERNAME=admin" >> .env
echo "_AIRFLOW_WWW_USER_PASSWORD=admin" >> .env
```

> **Importante:** não use `sudo docker compose up`. Rodar como root cria pastas de log como `root:root` e gera `PermissionError`. Se isso ocorrer, execute:
>
> ```bash
> bash scripts/fix-permissions.sh
> docker compose up -d --scale airflow-worker=3
> ```

### 3. Subir toda a infraestrutura

```bash
docker compose up -d --build --scale airflow-worker=3
```

Aguarde o `airflow-init` concluir (primeira execução demora mais por causa do build e do MLflow).

> **Sobre as 3 réplicas:** o `docker-compose.yml` declara `deploy.replicas: 3`. Em Docker Compose standalone (sem Swarm), use `--scale airflow-worker=3` para garantir os três workers ativos.

### 4. Verificar saúde dos serviços

```bash
docker compose ps
```

Todos os containers devem estar `healthy` ou `running` (exceto `airflow-init`, que encerra com sucesso).

### 5. Acessar as interfaces

| Interface | URL | Credenciais |
|-----------|-----|-------------|
| Airflow | http://localhost:8080 | `admin` / `admin` |
| Flower | http://localhost:5555 | — |
| MLflow | http://localhost:5000 | — |

### 6. Executar o pipeline

1. No Airflow, localize a DAG `inflacao_alimentos_mlops` em `dags/`.
2. Ative a DAG e clique em **Trigger DAG**.
3. Acompanhe a execução na aba **Graph** e nos **logs** de cada task.
4. No **Flower**, confirme os **3 workers** processando tasks em paralelo.
5. No **MLflow**, verifique runs de treinamento com métricas e artefatos do modelo.
6. No PostgreSQL, consulte as tabelas de destino:

```bash
docker exec -it trabalho3-postgres psql -U ipca -d ipca -c \
  "SELECT produto, tendencia_alta, rmse, run_id, created_at
   FROM gold.tb_alerta_inflacao
   ORDER BY created_at DESC
   LIMIT 10;"
```

Conexão externa (DBeaver, psql local): `localhost:5432` — usuário `ipca`, senha `ipca`, banco `ipca`.

---

## Decisões técnicas

### Airflow com CeleryExecutor (e não LocalExecutor)

O pipeline envolve múltiplas etapas independentes (extração por alimento, transformações, treino e inferência). O **CeleryExecutor** distribui essas tasks entre **3 workers**, reduzindo tempo total de execução e demonstrando arquitetura profissional — requisito explícito do projeto final e evolução do Trabalho 2.

### PostgreSQL único com múltiplos databases

Para ambiente local, um container PostgreSQL com databases `airflow`, `mlflow` e `ipca` simplifica operação e backup, mantendo isolamento lógico por usuário/database. Em produção, esses backends seriam separados em instâncias distintas.

### Idempotência por `run_id`

As tabelas `bronze.raw_ipca` e `gold.predicoes_inflacao` possuem constraint `UNIQUE` incluindo `run_id` (identificador da execução Airflow). Reprocessar a mesma run não duplica registros; uma nova execução gera novo `run_id` e novos dados.

### Resiliência

Tasks críticas (extração da API IBGE) utilizam `retries` com backoff exponencial para lidar com indisponibilidade temporária da API. Callbacks de ciclo de vida registram falhas nos logs do Airflow.

### MLflow integrado ao orquestrador

O MLflow não roda isolado: tasks Airflow invocam treinamento/inferência e registram runs via `MLFLOW_TRACKING_URI=http://mlflow:5000`, atendendo ao requisito de que MLflow deve estar integrado a um orquestrador.

### Timezone

`America/Sao_Paulo` em scheduler e webserver — alinhado ao calendário de divulgação do IPCA pelo IBGE.

---

## Requisitos mínimos atendidos

| Requisito | Implementação |
|-----------|---------------|
| Agendamento / trigger | DAG com cron mensal + trigger manual na UI |
| Resiliência | Retries, backoff e callbacks nas tasks de ingestão |
| Idempotência | Constraints `UNIQUE` com `run_id` no PostgreSQL |
| Modularidade | Tasks/funções separadas em `dags/` e `plugins/` |
| Persistência | PostgreSQL (Bronze/Silver/Gold) + MLflow artifacts |
| Observabilidade | UI Airflow, Flower (workers) e MLflow (experimentos) |
| Dockerizado | `docker compose up` sobe toda a stack |

---

## Comandos úteis

```bash
# Logs em tempo real
docker compose logs -f airflow-scheduler airflow-worker mlflow

# Rebuild após alterar Dockerfile ou dependências
docker compose up -d --build --scale airflow-worker=3

# Ver workers ativos no Celery
docker compose exec airflow-worker \
  celery --app airflow.providers.celery.executors.celery_executor.app inspect active

# Derrubar stack (preserva volumes)
docker compose down

# Derrubar e apagar volumes (reset completo)
docker compose down -v
```

---

## Entrega do projeto final

| Item | Status |
|------|--------|
| Repositório GitHub/GitLab | [and6rj/PucMinas — Trabalho3](https://github.com/and6rj/PucMinas/tree/main/Orquestracao_Workflow/Trabalho3_AndreOliveira) |
| Documentação (este README) | ✅ |
| Pitch em vídeo (5–10 min) | _link a publicar_ |

**Acesso ao professor:** incluir usuário `reinaldocm-prof` no repositório (se privado).

**Pitch — roteiro sugerido:**
1. Problema: monitoramento da inflação de alimentos básicos.
2. Arquitetura: Airflow distribuído + MLflow + PostgreSQL Medallion.
3. Demo: `docker compose up`, trigger da DAG, Flower com 3 workers, MLflow com métricas.
4. Decisões: CeleryExecutor, idempotência, integração MLflow.

---

## Referências

- [Enunciado do Projeto Final](TRABALHO_FINAL_ORQUESTRACAO.pdf)
- [API SIDRA — IBGE](https://apisidra.ibge.gov.br/)
- [Documentação Apache Airflow](https://airflow.apache.org/docs/)
- [Documentação MLflow](https://mlflow.org/docs/latest/)
