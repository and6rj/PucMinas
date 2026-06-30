# Trabalho 1 — Containerização com Docker Compose

Implementação da estrutura containerizada para o jogo de adivinhação [guess_game](https://github.com/fams/guess_game), desenvolvido originalmente em **Python 3.12** (Flask) e **Node 18.17** (React).

Este projeto **não altera o código-fonte** do jogo. Toda a containerização foi feita por meio de Dockerfiles, configuração do NGINX e orquestração com Docker Compose.

---

## Índice

1. [Visão geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação](#instalação)
4. [Uso](#uso)
5. [Decisões de design](#decisões-de-design)
6. [Estrutura do projeto](#estrutura-do-projeto)
7. [Referência de configuração](#referência-de-configuração)
8. [Testes e verificação](#testes-e-verificação)
9. [Manutenção e atualização](#manutenção-e-atualização)
10. [Solução de problemas](#solução-de-problemas)

---

## Visão geral

O desafio consiste em orquestrar três serviços com Docker Compose:

| Serviço    | Container        | Tecnologia            | Papel                                           |
|------------|------------------|-----------------------|-------------------------------------------------|
| `db`       | `postgres_db`    | PostgreSQL 15 Alpine  | Armazenamento persistente dos jogos             |
| `backend`  | 3 réplicas Flask | Python 3.12 + Flask   | API REST (`/create`, `/guess/<id>`, `/health`)  |
| `frontend` | `frontend`       | NGINX + React (build) | Proxy reverso e entrega das páginas estáticas   |

### Arquitetura

```
                    ┌─────────────────────────────────────────┐
                    │              Host (porta 80)            │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │  frontend (NGINX) — rede front-tier       │
                    │  • Serve arquivos estáticos do React      │
                    │  • Proxy reverso para a API               │
                    │  • Balanceamento entre réplicas backend   │
                    └─────────────┬───────────────────────────┘
                                  │  /create, /guess/*, /health
                    ┌─────────────▼───────────────────────────┐
                    │  backend × 3 (Flask) — rede back-tier   │
                    └─────────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────────┐
                    │  db (PostgreSQL) — rede back-tier       │
                    │  volume persistente: db-data              │
                    └─────────────────────────────────────────┘
```

O usuário acessa **apenas a porta 80** do host. O backend e o banco de dados **não são expostos** diretamente — ficam acessíveis somente na rede interna Docker.

---

## Pré-requisitos

| Requisito        | Versão mínima | Verificação              |
|------------------|---------------|--------------------------|
| Docker Engine    | 20.10+        | `docker --version`       |
| Docker Compose   | v2            | `docker compose version` |
| Git (opcional)   | —             | Para clonar o repositório |

> **Versões do runtime:** Node **18.17** e Python **3.12** estão fixadas nos Dockerfiles. Alterações de versão são desencorajadas e desnecessárias para a entrega, pois o projeto original foi desenvolvido e testado com essas versões.

---

## Instalação

### 1. Obter o projeto

Se ainda não tiver os arquivos localmente:

```bash
git clone <url-do-seu-repositorio>
cd Trabalho1
```

Certifique-se de que a pasta `guess_game/` contém o código-fonte original do jogo (backend Flask + frontend React).

### 2. Conferir a estrutura

Antes de subir os containers, verifique se os arquivos de infraestrutura estão presentes:

```
Trabalho1/
├── docker-compose.yml
├── guess_game/
│   ├── Dockerfile
│   ├── run.py
│   ├── requirements.txt
│   └── frontend/
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
└── README.md
```

### 3. Construir e iniciar os containers

Na raiz do projeto (`Trabalho1/`):

```bash
docker compose up --build -d
```

Esse comando:

1. Constrói a imagem do **backend** (Python 3.12 + dependências Flask).
2. Constrói a imagem do **frontend** (compila o React com Node 18.17 e empacota no NGINX).
3. Baixa a imagem do **PostgreSQL 15**.
4. Cria as redes, volumes e inicia todos os serviços.

### 4. Aguardar a inicialização

```bash
docker compose ps
```

Saída esperada: `postgres_db` com status **healthy**, 3 containers `backend` e `frontend` **Up**.

Para acompanhar os logs em tempo real:

```bash
docker compose logs -f
```

Para logs de um serviço específico:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

---

## Uso

### Acesso via navegador

Abra no browser:

**http://localhost:80**

#### Criar um jogo

1. Clique em **Create a Game** (rota `/maker`).
2. Digite uma frase secreta e envie.
3. Anote o **Game ID** exibido na tela.

#### Adivinhar a senha

1. Clique em **Join a Game** (rota `/breaker`).
2. Informe o **Game ID** recebido.
3. Digite sua tentativa e envie.
4. O sistema retorna se a adivinhação está correta ou dicas sobre letras e posições.

### Acesso via API (curl)

#### Verificar saúde da API

```bash
curl http://localhost/health
```

Resposta esperada:

```json
{"status":"ok"}
```

#### Criar um jogo

```bash
curl -X POST http://localhost/create \
  -H "Content-Type: application/json" \
  -d '{"password":"minhasenha"}'
```

Resposta esperada:

```json
{"game_id":"AbCdEf12"}
```

#### Enviar uma adivinhação

Substitua `GAME_ID` pelo valor retornado na criação:

```bash
curl -X POST http://localhost/guess/GAME_ID \
  -H "Content-Type: application/json" \
  -d '{"guess":"minhasenha"}'
```

Resposta esperada (acerto):

```json
{"result":"Correct"}
```

### Parar a aplicação

Encerrar os containers mantendo os dados do banco:

```bash
docker compose down
```

Encerrar e **apagar** o volume do PostgreSQL (remove todos os jogos salvos):

```bash
docker compose down -v
```

---

## Decisões de design

Esta seção documenta **por que** cada escolha arquitetural foi adotada.

### 1. Separação em três serviços

Cada componente roda em seu próprio container, conforme exigido pelo desafio:

- **Backend (Flask):** responsável exclusivamente pela lógica de negócio e API.
- **Banco (PostgreSQL):** responsável exclusivamente pela persistência.
- **Frontend (NGINX):** responsável pela entrega do React e pelo proxy reverso.

Isso permite escalar, atualizar e reiniciar cada camada de forma independente.

### 2. Código-fonte intacto

Nenhum arquivo dentro de `guess_game/` foi modificado. A integração com containers é feita por:

- Variáveis de ambiente no `docker-compose.yml` (prefixo `FLASK_`, lido nativamente pelo Flask).
- Dockerfiles que apenas copiam e executam o código existente.
- Build do React com `REACT_APP_BACKEND_URL=http://localhost` no `nginx/Dockerfile`.

Essa abordagem respeita o requisito de não alterar o fonte e reduz risco de regressão.

### 3. NGINX como proxy reverso (e não container React separado)

Em vez de rodar o React com `npm start` em um container de desenvolvimento, o frontend é **compilado em build de produção** e servido pelo NGINX.

**Motivos:**

- Menor consumo de recursos (sem processo Node em runtime).
- NGINX é mais eficiente para arquivos estáticos.
- O mesmo container NGINX faz **proxy reverso** das rotas de API (`/create`, `/guess/`, `/health`) para o backend.
- O browser acessa tudo pela mesma origem (`http://localhost`), evitando problemas de CORS e mixed content.

### 4. `REACT_APP_BACKEND_URL=http://localhost`

O React chama a API usando essa variável de ambiente, definida **no momento do build** (não em runtime).

Como o NGINX escuta na porta 80 do host e encaminha `/create` e `/guess/` para o Flask, o browser faz requisições para `http://localhost/create` — mesma origem da página. Não é necessário expor a porta 5000 do Flask ao host.

### 5. Duas redes Docker (`front-tier` e `back-tier`)

| Rede          | Serviços conectados     | Função                                      |
|---------------|-------------------------|---------------------------------------------|
| `front-tier`  | `frontend`              | Isola a exposição pública (porta 80)        |
| `back-tier`   | `frontend`, `backend`, `db` | Comunicação interna entre serviços      |

O NGINX participa das **duas redes**: recebe tráfego externo e alcança o backend internamente. O banco de dados fica **somente** na `back-tier`, sem acesso direto do host.

### 6. Backend com 3 réplicas e balanceamento no NGINX

```yaml
deploy:
  replicas: 3
```

O Docker Compose cria três instâncias idênticas do Flask. O NGINX distribui as requisições entre elas usando:

- **`upstream backend`** com algoritmo **`least_conn`** (envia para a réplica com menos conexões ativas).
- **`resolver 127.0.0.11`** — DNS interno do Docker, que resolve o nome `backend` para os IPs de todas as réplicas.
- **`server backend:5000 resolve`** — redescoberta dinâmica das instâncias sem reiniciar o NGINX.
- **`max_fails` + `proxy_next_upstream`** — se uma réplica falhar, o NGINX tenta outra automaticamente.

**Motivo:** atender ao requisito de resiliência e balanceamento de carga sem alterar o código Flask.

### 7. Volume nomeado para o PostgreSQL

```yaml
volumes:
  - db-data:/var/lib/postgresql/data
```

Os dados do banco ficam em um volume Docker **separado** do ciclo de vida do container. Recriar o container `postgres_db` não apaga os jogos salvos. Somente `docker compose down -v` remove o volume.

### 8. Healthcheck no banco antes do backend

```yaml
depends_on:
  db:
    condition: service_healthy
```

O backend só inicia após o PostgreSQL responder ao `pg_isready`. Isso evita falhas de conexão na subida (`the database system is starting up`) e garante ordem de inicialização confiável.

### 9. Política `restart: unless-stopped`

Todos os serviços usam `restart: unless-stopped`. Se um container encerrar por falha, o Docker o reinicia automaticamente. Containers parados manualmente (`docker compose stop`) não são reiniciados.

### 10. Versões fixas de runtime

| Componente | Imagem base              | Motivo                                      |
|------------|--------------------------|---------------------------------------------|
| Backend    | `python:3.12-slim`       | Compatível com o projeto original (3.8–3.12) |
| Frontend   | `node:18.17-alpine`      | Versão exigida pelo README do guess_game    |
| Banco      | `postgres:15-alpine`     | Estável, leve, adequada para produção local |
| Proxy      | `nginx:alpine`           | Leve e eficiente para estáticos + proxy     |

Alterar essas versões não é necessário para a entrega e pode introduzir incompatibilidades.

### 11. Backend não exposto ao host

O backend usa `expose: "5000"` (rede interna), não `ports`. Apenas o NGINX é acessível externamente. Isso reforça o papel do proxy reverso como **único ponto de entrada**.

---

## Estrutura do projeto

```
Trabalho1/
├── docker-compose.yml          # Orquestração: serviços, redes, volumes
├── README.md                   # Esta documentação
│
├── guess_game/                 # Código-fonte original (sem alterações)
│   ├── Dockerfile              # Imagem Python 3.12 + Flask
│   ├── run.py                  # Entry point da aplicação
│   ├── requirements.txt        # Dependências Python
│   ├── guess/                  # Rotas e lógica do jogo
│   ├── repository/             # Camada de persistência (Postgres, etc.)
│   └── frontend/               # Aplicação React
│
└── nginx/
    ├── Dockerfile              # Build multi-stage: Node 18 → NGINX
    └── nginx.conf              # Proxy reverso + balanceamento + SPA
```

---

## Referência de configuração

### Variáveis de ambiente do backend

O Flask lê variáveis com prefixo `FLASK_` via `app.config.from_prefixed_env()`:

| Variável              | Valor        | Descrição                    |
|-----------------------|--------------|------------------------------|
| `FLASK_APP`           | `run.py`     | Arquivo de entrada           |
| `FLASK_DB_TYPE`       | `postgres`   | Driver de banco              |
| `FLASK_DB_HOST`       | `db`         | Hostname do serviço Postgres |
| `FLASK_DB_PORT`       | `5432`       | Porta do Postgres            |
| `FLASK_DB_USER`       | `postgres`   | Usuário do banco             |
| `FLASK_DB_NAME`       | `postgres`   | Nome do banco                |
| `FLASK_DB_PASSWORD`   | `secretpass` | Senha do banco               |

### Rotas da API (via NGINX)

| Método | Rota              | Descrição                          |
|--------|-------------------|------------------------------------|
| GET    | `/health`         | Verifica se a API está operacional |
| POST   | `/create`         | Cria um jogo e retorna `game_id`   |
| POST   | `/guess/<game_id>`| Envia uma tentativa de adivinhação |

### Rotas do frontend (React SPA)

| Rota       | Componente | Descrição              |
|------------|------------|------------------------|
| `/`        | Home       | Página inicial         |
| `/maker`   | Maker      | Criar novo jogo        |
| `/breaker` | Breaker    | Adivinhar a senha      |

Demais rotas são tratadas pelo NGINX com `try_files` → `index.html` (comportamento padrão de SPA).

---

## Testes e verificação

### Checklist rápido após instalação

```bash
# 1. Todos os containers rodando
docker compose ps

# 2. Três réplicas do backend
docker compose ps | grep backend

# 3. API respondendo
curl http://localhost/health

# 4. Fluxo completo
curl -X POST http://localhost/create \
  -H "Content-Type: application/json" \
  -d '{"password":"teste123"}'
# Copie o game_id retornado e use no comando abaixo:
curl -X POST http://localhost/guess/GAME_ID \
  -H "Content-Type: application/json" \
  -d '{"guess":"teste123"}'

# 5. Frontend servindo HTML
curl -s http://localhost/ | head -5
```

### Verificar balanceamento de carga

Confirme que o DNS interno resolve múltiplas réplicas:

```bash
docker exec frontend nslookup backend 127.0.0.11
```

Deve retornar **3 endereços IP** distintos.

### Testar resiliência (opcional)

```bash
# Parar uma réplica
docker stop trabalho1-backend-1

# A API deve continuar respondendo
curl http://localhost/health

# Reiniciar a réplica
docker start trabalho1-backend-1
```

---

## Manutenção e atualização

A estrutura permite atualizar cada componente de forma independente:

| Componente | Como atualizar                                      |
|------------|-----------------------------------------------------|
| Backend    | `docker compose build backend && docker compose up -d backend` |
| Frontend   | `docker compose build frontend && docker compose up -d frontend` |
| Banco      | Alterar tag em `image: postgres:15-alpine` no compose |

Para alterar o número de réplicas do backend, modifique `deploy.replicas` no `docker-compose.yml` e execute:

```bash
docker compose up -d
```

O NGINX redescobre as instâncias automaticamente via DNS interno.

---

## Solução de problemas

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| `connection refused` na porta 80 | Containers não iniciados | `docker compose up -d` e aguarde |
| Backend reiniciando em loop | Postgres ainda não pronto | Aguarde `postgres_db` ficar `healthy`; verifique logs com `docker compose logs db` |
| Página em branco no browser | Build do frontend falhou | `docker compose build frontend --no-cache` |
| `Game not found` | Game ID incorreto ou banco resetado | Crie um novo jogo; evite `docker compose down -v` se quiser manter dados |
| Porta 80 ocupada | Outro serviço usando a porta | Pare o serviço conflitante ou altere `"80:80"` no compose |
| Erro ao criar jogo no browser | Build antigo do React | Reconstrua o frontend: `docker compose build frontend && docker compose up -d frontend` |

Para reiniciar toda a stack do zero (mantendo dados):

```bash
docker compose down
docker compose up --build -d
```

---

## Referências

- Repositório original do jogo: [github.com/fams/guess_game](https://github.com/fams/guess_game)
- Documentação Docker Compose: [docs.docker.com/compose](https://docs.docker.com/compose/)
- Documentação NGINX (proxy reverso): [nginx.org/en/docs/http/ngx_http_proxy_module.html](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
