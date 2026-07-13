# Trabalho 2 — Trabalho Prático Unidade Kubernetes

**Aluno:** André Cardoso de Oliveira  
**Pasta:** `Conteinerizacao_Kubernets/Trabalho2_AndreOliveira`  
**Repositório:** https://github.com/and6rj/PucMinas/tree/main/Conteinerizacao_Kubernets/Trabalho2_AndreOliveira

Implementação em **Kubernetes** da stack containerizada do jogo `guess_game`, sem Ingress Controller.

O usuário acessa o sistema pela **porta do frontend** via `kubectl port-forward`.

Este diretório é **autossuficiente**: inclui o código-fonte do jogo, Dockerfiles e manifests Kubernetes.

---

## Índice

1. [Visão geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação](#instalação)
4. [Uso](#uso)
5. [Decisões de design](#decisões-de-design)
6. [Estrutura do projeto](#estrutura-do-projeto)
7. [Mapeamento Docker Compose → Kubernetes](#mapeamento-docker-compose--kubernetes)
8. [Testes e verificação](#testes-e-verificação)

---

## Visão geral

| Componente   | Recurso Kubernetes                         | Papel                                              |
|--------------|--------------------------------------------|----------------------------------------------------|
| `db`         | Deployment + PVC + Service `db`            | PostgreSQL 15 (persistência)                       |
| `backend`    | Deployment + Service + HPA (3–10 réplicas) | API Flask (`/create`, `/guess/<id>`, `/health`)    |
| `frontend`   | Deployment + Service `frontend`            | NGINX: estáticos React + proxy reverso para a API  |
| credenciais  | Secret `postgres-secret`                   | Usuário/senha/banco do Postgres                    |

### Arquitetura

```
                         Host (port-forward 8081 → 80)
                                      │
                    ┌─────────────────▼─────────────────┐
                    │  Service/frontend (ClusterIP :80) │
                    │  Deployment frontend (NGINX)      │
                    │  • Serve build React              │
                    │  • Proxy /create, /guess/, /health│
                    └─────────────────┬─────────────────┘
                                      │  DNS: backend:5000
                    ┌─────────────────▼─────────────────┐
                    │  Service/backend (ClusterIP)      │
                    │  Deployment backend (Flask)       │
                    │  HPA: 3–10 réplicas (CPU/mem)     │
                    └─────────────────┬─────────────────┘
                                      │  DNS: db:5432
                    ┌─────────────────▼─────────────────┐
                    │  Service/db + PVC postgres-pvc    │
                    │  Deployment postgres              │
                    └───────────────────────────────────┘
```

Namespace: **`guess-game`**. Backend e banco **não** são expostos ao host — apenas o frontend, via port-forward.

---

## Pré-requisitos

| Requisito        | Verificação                    |
|------------------|--------------------------------|
| Docker Engine    | `docker --version`             |
| kubectl          | `kubectl version --client`     |
| Cluster local    | ex.: contexto `k3d-meu-cluster` |

### Imagens no Docker Hub (públicas)

| Papel     | Imagem |
|-----------|--------|
| Backend   | `and6rj/and6rj-guess-game-backend:latest` |
| Frontend  | `and6rj/and6rj-guess-game-frontend:latest` |

Os Deployments usam `imagePullPolicy: Always` e puxam essas imagens do Hub. **Não é necessário rebuild nem `k3d image import`** no dia a dia.

---

## Instalação

### 1. Ir para a pasta do Trabalho 2

```bash
cd Conteinerizacao_Kubernets/Trabalho2_AndreOliveira
chmod +x apply.sh push-images.sh build-images.sh
```

### 2. Publicar as imagens no Hub (somente na primeira vez)

As imagens ainda precisam existir no Hub uma vez:

```bash
docker login
./push-images.sh
```

Isso faz build + `docker push` de:

- `and6rj/and6rj-guess-game-backend:latest`
- `and6rj/and6rj-guess-game-frontend:latest`

Depois disso, qualquer máquina/cluster só precisa do `kubectl apply`.

### 3. Apontar para o cluster e aplicar

```bash
kubectl config use-context k3d-meu-cluster
./apply.sh
```

Ou:

```bash
kubectl apply -f k8s/
```

### 4. Conferir o status

```bash
kubectl get pods,svc,hpa -n guess-game
```

Esperado: pods de `postgres`, `backend` (≥3) e `frontend` em **Running/Ready**, Services `db`, `backend` e `frontend` do tipo **ClusterIP**, e HPA `backend` ativo.

> **Metrics Server:** o HPA precisa do Metrics Server no cluster (`kubectl top pods` deve funcionar).
---

## Uso

### Acesso via port-forward (frontend)

```bash
kubectl port-forward -n guess-game svc/frontend 8081:80
```

Abra no browser: **http://localhost:8081**

O fluxo do jogo: Create a Game / Join a Game no browser.

### API via curl

```bash
curl http://localhost:8081/health

curl -X POST http://localhost:8081/create \
  -H "Content-Type: application/json" \
  -d '{"password":"minhasenha"}'

curl -X POST http://localhost:8081/guess/GAME_ID \
  -H "Content-Type: application/json" \
  -d '{"guess":"minhasenha"}'
```

### Encerrar

Parar o port-forward: `Ctrl+C`.

Remover os recursos do cluster:

```bash
kubectl delete namespace guess-game
```

Isso remove Deployments, Services, Secret e o PVC (dados do banco).

---

## Decisões de design

### 1. Mesma arquitetura de três camadas

Três camadas: **frontend (NGINX)**, **backend (Flask × 3)** e **PostgreSQL**. A containerização e a orquestração não alteram a lógica do `guess_game`.

### 2. Sem Ingress Controller

Conforme o enunciado: acesso direto à porta do frontend. O Service `frontend` é **ClusterIP**; a exposição ao host é feita com:

```bash
kubectl port-forward -n guess-game svc/frontend 8081:80
```

### 3. Service do backend como balanceador

O **Service `backend`** (ClusterIP) distribui o tráfego entre os Pods do Deployment (kube-proxy / IPVS). O NGINX aponta para `backend:5000` e mantém `least_conn` + `proxy_next_upstream` como reforço.

### 3.1. AutoScale com HPA no backend

O arquivo `k8s/05-backend-hpa.yaml` define um **HorizontalPodAutoscaler** sobre o Deployment `backend`:

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| `minReplicas` | 3 | Mantém a resiliência mínima do laboratório |
| `maxReplicas` | 10 | Limite superior sob carga |
| CPU | 50% de utilização média | Escala quando a média dos pods passa do alvo |
| Memória | 70% de utilização média | Segundo critério de escala |

O Deployment declara `resources.requests` (e `limits`) — obrigatório para o HPA calcular utilização. Com o HPA ativo, ele passa a controlar o número de réplicas (o campo `replicas: 3` do Deployment é só o valor inicial).

### 4. `REACT_APP_BACKEND_URL=http://localhost:8081`

O browser fala com a mesma origem do port-forward; o NGINX encaminha `/create`, `/guess/` e `/health` para o Service interno `backend`. Evita CORS e exposição da porta 5000.

### 5. Secret para credenciais

As variáveis `POSTGRES_*` / `FLASK_DB_*` sensíveis ficam no Secret `postgres-secret`, referenciadas pelos Deployments de Postgres e backend.

### 6. PVC para persistência

O volume nomeado `db-data` do Compose vira o **PersistentVolumeClaim** `postgres-pvc` (1 Gi, `ReadWriteOnce`), montado em `/var/lib/postgresql/data`.

### 7. Probes de readiness/liveness

- Postgres: `pg_isready`
- Backend: `GET /health`
- Frontend: `GET /`

O backend só recebe tráfego do Service quando estiver Ready; o frontend espera o backend via DNS do cluster (e retries do proxy).

### 8. Namespace `guess-game`

Isola todos os recursos do laboratório e facilita limpeza com um único `kubectl delete namespace`.

---

## Estrutura do projeto

```
Trabalho2_AndreOliveira/
├── README.md
├── apply.sh                 # aplica manifests e aguarda Ready
├── push-images.sh           # build + push para o Docker Hub (uma vez)
├── build-images.sh          # build local opcional (sem push)
├── guess_game/              # código-fonte do jogo (Flask + React)
│   └── Dockerfile           # imagem do backend
├── nginx/
│   ├── Dockerfile           # multi-stage: Node build + NGINX
│   └── nginx.conf           # proxy para Service backend:5000
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-secret.yaml
    ├── 02-postgres.yaml     # PVC + Deployment + Service db
    ├── 03-backend.yaml      # Deployment ×3 + Service backend
    ├── 04-frontend.yaml     # Deployment + Service frontend
    └── 05-backend-hpa.yaml  # HPA do backend (CPU/memória)
```

---

## Mapeamento Docker Compose → Kubernetes

| Docker Compose              | Kubernetes                                      |
|-----------------------------|-------------------------------------------------|
| `services.db`               | Deployment `postgres` + Service `db`            |
| `volumes: db-data`          | PVC `postgres-pvc`                              |
| `services.backend` ×3       | Deployment `backend` + HPA (3–10)               |
| DNS `backend` / rede Docker | Service ClusterIP `backend`                     |
| `services.frontend`         | Deployment `frontend` + Service `frontend`      |
| `ports: "8081:80"`          | `kubectl port-forward ... 8081:80`              |
| `environment` / senha       | Secret `postgres-secret`                        |
| redes `front-tier`/`back-tier` | Isolamento por namespace + Services internos |

---

## Testes e verificação

```bash
# Pods, Services e HPA
kubectl get all,hpa -n guess-game

# Detalhe do autoscaler
kubectl describe hpa backend -n guess-game

# Uso de CPU/memória (requer Metrics Server)
kubectl top pods -n guess-game -l app=backend

# Logs
kubectl logs -n guess-game -l app=backend --tail=50
kubectl logs -n guess-game -l app=frontend --tail=50
kubectl logs -n guess-game -l app=postgres --tail=50

# Health via port-forward (em outro terminal)
kubectl port-forward -n guess-game svc/frontend 8081:80
curl http://localhost:8081/health
```

Resposta esperada: `{"status":"ok"}`.

---

## Limpeza completa

```bash
kubectl delete namespace guess-game
```
