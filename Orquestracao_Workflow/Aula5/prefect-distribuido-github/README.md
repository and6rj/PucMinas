# Prefect distribuído com GitHub

Variante em que **o código do flow mora no GitHub**, não na imagem do worker.
O worker faz `git clone` do repositório na hora de executar cada run. Atualizar o
flow vira `git push` — sem rebuildar imagem, sem redeploy.

Quatro responsabilidades, quatro lugares:

| Peça | Onde mora |
|---|---|
| Código (`flows/`) | GitHub |
| Dependências (libs) | imagem do worker |
| Orquestração | `prefect-distribuido-scheduler` |
| Execução | máquina(s) do worker |

---

## Estrutura

```
prefect-distribuido-github/
├── docker-compose.worker.yml    # worker(s) — sem código embutido
├── Dockerfile.worker            # python + git + dependências (sem flows/)
├── requirements.txt             # libs do flow (continuam na imagem)
├── .env.example                 # PREFECT_API_URL + GITHUB_REPO
├── .gitignore                   # exclui .env e .venv
├── deploy.py                    # from_source(GitHub) .deploy() — roda no HOST
└── flows/
    ├── clima.py                 # @flow / @task — análise de clima
    └── example_4_map.py         # @flow / @task — fan-out / fan-in
```

---

## Pré-requisitos

- Docker + Docker Compose
- Scheduler rodando (`prefect-distribuido-scheduler`)
- Repositório público no GitHub com a pasta `flows/`
- `.venv` com Prefect instalado no host (para rodar o `deploy.py`)

---

## Configuração inicial (uma vez só)

### 1. Subir o repo para o GitHub

```bash
git init
git add .
git commit -m "flow inicial"
git remote add origin https://github.com/SEU-USUARIO/SEU-REPO.git
git push -u origin main
```

### 2. Criar o `.venv` no host

```bash
# com uv (recomendado)
uv venv
source .venv/bin/activate
uv pip install prefect

# ou com pip
python3 -m venv .venv
source .venv/bin/activate
pip install prefect
```

### 3. Configurar o `.env`

```bash
cp .env.example .env
```

Edite o `.env`:

```bash
# Workers dentro do Docker
PREFECT_API_URL=http://host.docker.internal:4230/api

# Repositório GitHub com o código do flow
GITHUB_REPO=https://github.com/SEU-USUARIO/SEU-REPO.git
```

---

## Passo a passo

```bash
# 1) Buildar a imagem do worker (python + git + deps, sem flows/)
docker compose -f docker-compose.worker.yml build

# 2) Registrar os deployments — roda no HOST via .venv
source .venv/bin/activate
PREFECT_API_URL="http://localhost:4230/api" python deploy.py

# 3) Subir os workers (clonam o repo em runtime)
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=3
```

Acesse a UI do scheduler (`http://localhost:4230`) → **Deployments** para
confirmar que os deployments apareceram com status `Ready`.

---

## Disparar runs

Pela UI: **Deployments** → deployment desejado → **Quick Run**.

Ou pelo terminal (com `.venv` ativo):

```bash
PREFECT_API_URL="http://localhost:4230/api" prefect deployment run "analise-clima/clima-github"
```

Nos logs do worker você verá o `git clone` antes da execução:

```bash
docker compose -f docker-compose.worker.yml logs -f
```

---

## Atualizar o código de um flow (o ponto-chave deste modelo)

```bash
# edite flows/clima.py ou flows/example_4_map.py
git add .
git commit -m "ajuste no flow"
git push
# a PRÓXIMA run já usa a versão nova — sem rebuildar a imagem
```

---

## Adicionar um flow novo

Quando adicionar um novo arquivo em `flows/`, dois passos são necessários:

```bash
# 1) Push do novo arquivo
git add flows/novo_flow.py
git commit -m "adiciona novo_flow"
git push

# 2) Atualizar o deploy.py com o novo deployment e registrar
source .venv/bin/activate
PREFECT_API_URL="http://localhost:4230/api" python deploy.py
```

> O `deploy.py` registra **metadados** no backend (nome, schedule, onde está
> o código). O código em si fica no GitHub. São dois ciclos separados:
> `git push` atualiza o código; `deploy.py` registra um flow novo ou muda
> configuração de deployment.

---

## O que precisa de rebuild

| O que mudou | rebuild | deploy.py |
|---|---|---|
| Código de um flow existente | ❌ | ❌ — só git push |
| Flow novo adicionado | ❌ | ✅ |
| Configuração do deployment (cron, nome) | ❌ | ✅ |
| Dependência (`requirements.txt`) | ✅ | ❌ |
| `Dockerfile.worker` | ✅ | ❌ |

Rebuild só quando mudar a **imagem** — dependências ou Dockerfile.
Código do flow nunca exige rebuild neste modelo.

---

## Rodar workers em outra máquina

Na máquina 2 (com este repo):

```bash
cp .env.example .env
# edite .env: PREFECT_API_URL=http://IP-DO-SCHEDULER:4230/api
#             GITHUB_REPO=https://github.com/SEU-USUARIO/SEU-REPO.git
docker compose -f docker-compose.worker.yml build
docker compose -f docker-compose.worker.yml up -d --scale prefect-worker=2
```

Os workers desta máquina também clonam o código do GitHub — o repo é a
fonte única de verdade para todos os workers, em qualquer máquina.

---

## Repositório privado

1. Crie um PAT (Personal Access Token) no GitHub com permissão de leitura.
2. Salve num Secret Block:

```python
from prefect.blocks.system import Secret
Secret(value="ghp_seu_token").save("github-token")
```

3. No `deploy.py`, use `GitRepository` com credenciais:

```python
from prefect.runner.storage import GitRepository
from prefect.blocks.system import Secret

source = GitRepository(
    url=GITHUB_REPO,
    branch="main",
    credentials={"access_token": Secret.load("github-token")},
)

flow.from_source(
    source=source,
    entrypoint="flows/clima.py:analise_clima_multiplas_cidades",
).deploy(...)
```

---

## Parar tudo

```bash
docker compose -f docker-compose.worker.yml down
```

---

## Notas

- **git na imagem**: obrigatório — sem ele o clone falha com `git: not found`.
  Já incluído no `Dockerfile.worker` via `apt-get install git`.
- **dependências ≠ código**: `from_source` traz só o código. Libs ficam na
  imagem — mudou lib → rebuild da imagem.
- **rede dos workers**: precisam alcançar `github.com` (clone) e a API do
  flow (open-meteo, fakestoreapi).
- **branch fixa**: use `GitRepository(url=..., branch="main")` para garantir
  que todos os workers clonam a mesma branch, mesmo em repos com múltiplas
  branches.
- **Versão fixada**: scheduler e workers usam `prefecthq/prefect:3.4.24-python3.12`.
  Versões diferentes entre server e worker podem causar incompatibilidade.
