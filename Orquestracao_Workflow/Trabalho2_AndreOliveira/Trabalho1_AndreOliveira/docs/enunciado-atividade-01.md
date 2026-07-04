# ATIVIDADE 01 — AIRFLOW

## 1. Contexto

Você acaba de assumir como líder técnico (tech lead) do time de dados da ShopBrasil, um marketplace de e-commerce em rápido crescimento.

Todas as manhãs, antes que a equipe de pricing e os gerentes de categoria comecem o expediente, eles abrem um painel com o panorama de preços por categoria — preço médio, mínimo, máximo e quantidade de produtos — para decidir as promoções e reposições do dia. Atualmente esse painel é alimentado por um script Python, agendado via cron, que busca os dados de uma API de catálogo.

### 1.1. Situação Problema

A arquitetura atual é frágil, pois:

- Quando a API oscila de madrugada, o script falha silenciosamente e o time fica sem dados.
- Quando alguém o roda "na mão" de novo, os números aparecem duplicados na base de dados.
- A cada nova categoria que surge, é preciso editar o código linha a linha.

Com isso temos uma arquitetura que não escala, não é confiável e ninguém dorme tranquilo.

## 2. Objetivo

Sua missão é projetar e conduzir seu time na construção de um pipeline de verdade no Apache Airflow, que aposente esse script executado via cron.

O pipeline deve coletar os produtos da API de catálogo (representada aqui pela FakeStore API), calcular as métricas por categoria e gravar o resultado na base analítica em PostgreSQL. Como tech lead, você não só implementa a referência, mas define os padrões que o time vai seguir.

Na prática, o pipeline precisa:

- Rodar sozinho todo dia às **06:00** (horário de Brasília), antes de o time chegar.
- Resistir às instabilidades da API, retentando com calma e sem derrubar a execução inteira.
- Escalar sozinho à medida que novas categorias aparecem.
- Nunca duplicar dados quando for reprocessado.
- Avisar quando algo falhar.
- Ser modular e legível, para que qualquer pessoa do time consiga manter.

## 3. Requisitos obrigatórios

### Fonte de Dados

- API: https://fakestoreapi.com/docs
- Swagger da API da qual serão capturados os dados.

### Modelagem e estrutura

- Usar **TaskFlow API** (`@dag` / `@task`); dependências saem da chamada das funções.
- **XComs automáticos** via `return` (passar apenas dados pequenos entre tasks).
- O pipeline deve conter, de forma identificável, as topologias **linear**, **fan-out** (mapeamento por categoria) e **fan-in** (consolidação).

### Agendamento

- Timezone ancorado em `America/Sao_Paulo` (use `pendulum`), com `start_date` e `catchup=False`.

### Ingestão resiliente

- Task **"Buscar Produtos"** com retry e exponential backoff.
- Tratamento de erro com `try/except` + `raise` (para acionar o retry).
- Callbacks de ciclo de vida na task crítica: `on_failure_callback`, `on_retry_callback` e `on_success_callback`.

### Processamento paralelo

- Calcular métricas por categoria com **Dynamic Task Mapping** (`.expand(...)`).
- **Pool** para limitar a concorrência das tasks mapeadas (`pool ecommerce_pool` com 2 slots).

### Organização

- Agrupar as tasks em pelo menos **2 TaskGroups** (ex.: ingestão e análise).

### Persistência no PostgreSQL

- Criar Task que:
  - Salve os registros no Banco de Dados com consistência na inserção de dados para não gerar duplicidade de registros.
  - Use `PostgresHook` e uma Connection do Airflow.
- A gravação deve ser **idempotente**: re-rodar a mesma run não duplica linhas.
