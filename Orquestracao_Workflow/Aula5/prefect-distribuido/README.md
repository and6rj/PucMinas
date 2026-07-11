# Prefect distribuído (sem Kubernetes)

Dois repositórios, duas responsabilidades:

| Repo | Responsabilidade | Fica de pé? |
|---|---|---|
| `prefect-distribuido-scheduler` | orquestra (server + UI + postgres) | sim |
| `prefect-distribuido-workers` | executa os flows | sim (N réplicas) |

O código dos flows está **embutido na imagem do worker** (`COPY flows/`).
Para atualizar sem rebuildar, use o modelo `prefect-distribuido-github`.

---

## Estrutura

```
prefect-distribuido-workers/
├── docker-compose.worker.yml   # MAQUINA N: worker(s), escalável com --scale
├── Dockerfile.worker           # imagem do worker: python + deps + flows
├── requirements.txt            # deps extras do flow (prefect vem da imagem base)
├── .env.example                # PREFECT_API_URL (copie para .env)
├── deploy.py                   # registra os deployments no work pool
└── flows/
    └── clima.py                # @flow / @task de exemplo
```

---

## Pré-requisitos

- Docker + Docker Compose
- Scheduler rodando (`prefect-distribuido-scheduler`)
- `.env` configurado (veja abaixo)

---

## Configuração

```bash
cp .env.example .env
```

Edite o `.env` conforme o cenário:

```bash
# Cenário A — workers na MESMA máquina do scheduler:
PREFECT_API_URL=http://host.docker.internal:4201/api

# Cenário B — workers em OUTRA máquina:
# PREFECT_API_URL=http://IP-DO-SCHEDULER:4201/api
```

---

## Passo a passo

```bash
# 1) Buildar a imagem do worker
docker compose -f docker-compose.worker.yml build

# 2) Registrar os deployments no scheduler
#    (roda dentro da imagem para os caminhos baterem com o runtime do worker)
docker compose -f docker-compose.worker.yml run --rm prefect-worker python deploy.py

# 3) Subir os workers — aqui está a distribuição
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=3

# Confirmar que os 3 workers estão "Up"
docker compose -f docker-compose.worker.yml ps
```

Acesse a UI do scheduler (`http://localhost:4201`) → **Work Pools** → `lab-pool`
→ aba **Workers** para ver os workers online e o polling em tempo real.

---

## Disparar runs e ver a distribuição

```bash
# Disparar 6 runs de uma vez
for i in $(seq 1 6); do
  PREFECT_API_URL="http://localhost:4201/api" prefect deployment run "analise-clima/clima-distribuido"
done
```

Ou pela UI: **Deployments** → `clima-distribuido` → **Quick Run**.

Abra **Flow Runs** na UI: as runs são distribuídas entre os workers —
quem está livre pega a próxima. Confirme pelos logs:

```bash
docker compose -f docker-compose.worker.yml logs -f
```

---

## Rodar workers em OUTRA máquina (distribuição de verdade)

Na máquina 2 (com este repo):

```bash
cp .env.example .env
# edite .env: PREFECT_API_URL=http://IP-DO-SCHEDULER:4201/api
docker compose -f docker-compose.worker.yml build
docker compose -f docker-compose.worker.yml run --rm prefect-worker python deploy.py
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=2
```

Agora há workers em duas máquinas escutando o mesmo `lab-pool`. Requisitos:

- A porta `4201` do scheduler precisa estar acessível pela rede (firewall/SG).
- Os workers precisam de saída para a internet (o flow chama a API open-meteo).

---

## Atualizando o projeto

| O que mudou | build | up | deploy.py |
|---|---|---|---|
| Código do flow (`flows/`) | ✅ | ✅ | ✅ |
| Flow novo adicionado | ✅ | ✅ | ✅ |
| Só configuração (`deploy.py`) | ❌ | ❌ | ✅ |
| Dependência (`requirements.txt`) | ✅ | ✅ | ❌ |

### Mudou o código de um flow existente
```bash
docker compose -f docker-compose.worker.yml build
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=3
docker compose -f docker-compose.worker.yml run --rm prefect-worker python deploy.py
```

### Mudou só a configuração do deployment (`deploy.py`)
```bash
docker compose -f docker-compose.worker.yml run --rm prefect-worker python deploy.py
```

### Adicionou um flow novo
```bash
docker compose -f docker-compose.worker.yml build
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=3
docker compose -f docker-compose.worker.yml run --rm prefect-worker python deploy.py
```

### Mudou uma dependência (`requirements.txt`)
```bash
docker compose -f docker-compose.worker.yml build
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=3
```

> **Por que rebuild?** O código está embutido na imagem via `COPY flows/`.
> No modelo `prefect-distribuido-github`, `git push` é suficiente — o worker
> clona o repositório a cada run, sem precisar rebuildar a imagem.

---

## Controlar a vazão

O limite de concorrência define quantas runs rodam ao mesmo tempo
no total (somando todos os workers):

```bash
PREFECT_API_URL="http://localhost:4201/api" prefect work-pool set-concurrency-limit lab-pool 6
```

---

## Parar tudo

```bash
docker compose -f docker-compose.worker.yml down
```

---

## Notas

- **Tipo do pool = `process`**: cada run roda como subprocesso dentro do
  container do worker. Para infra efêmera por run (um container novo a cada
  execução), troque por um pool tipo `docker`.
- **Versão fixada**: scheduler e workers usam `prefecthq/prefect:3.4.24-python3.12`.
  Versões diferentes entre server e worker podem causar incompatibilidade.
- **Ponto único**: o scheduler (server + postgres) não está replicado aqui.
  HA do backend exigiria server atrás de load balancer + Postgres gerenciado.
- **Distribuição de tasks dentro de uma run**: troque o `task_runner` do flow
  por `DaskTaskRunner`/`RayTaskRunner` para paralelizar tasks de uma mesma run
  em múltiplas máquinas. Fora do escopo deste repo.
