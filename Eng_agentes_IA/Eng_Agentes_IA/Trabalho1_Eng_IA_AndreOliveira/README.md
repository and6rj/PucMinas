# Trabalho 1 — Agente único de análise rodoviária

**André Oliveira** · Engenharia de Agentes e IA Agêntica · Pós-graduação · PUC Minas

Entrega 1: um agente baseado em LLM, com ciclo de decisão, ação e observação, conhecimento e ferramentas em integração direta. Não usa MCP nem LangGraph. O único segredo é a chave `GEMINI_API_KEY`.

O arquivo da entrega é `Trabalho1_Agente_Unico_Rodoviario.ipynb`.

Notebook no Colab: https://colab.research.google.com/drive/12QvC1vQQBvBb7Pw5vnvlHGk50lNm6e6T?usp=sharing

## Como executar

1. Abra o notebook no Colab pelo link acima.
2. Em Secrets, crie `GEMINI_API_KEY` e libere o acesso do notebook. A chave não é gravada no arquivo.
3. Execute as células em ordem, da seção 3 até a demonstração.

A primeira execução baixa cerca de 730 MB dos CSVs. O cache fica em `/tmp` e vale para a sessão do Colab. As dependências são instaladas pela própria seção 3: `google-genai==2.29.0`, `pandas`, `numpy`, `jsonschema` e `gdown`.

A seção 9 percorre os modelos Flash até um responder. Se o embedding falhar, a busca de conhecimento segue no modo lexical.

## De onde vêm os dados

Os CSVs e os trechos de conhecimento não entram no Git. A execução baixa duas pastas públicas do Drive. As duas precisam permanecer compartilhadas como **qualquer pessoa com o link**.

| Uso | Pasta |
|---|---|
| Fatos | https://drive.google.com/drive/folders/1-1ckwMQA2OUvt0gMWf3pp5yx1PMStn2I |
| Conhecimento | https://drive.google.com/drive/folders/1TKIUYyCiG6UoHt8ihUyKsdmzyZwYdfHY |

- `ticket_viagem.csv`: um bilhete por linha. Receita, quantidade de passagens, canal, antecedência e passageiro-quilômetro.
- `ocupacao.csv`: uma perna por linha. Ocupantes, capacidade, vagas, embarque, desembarque e excesso.
- Conhecimento: sete arquivos `.txt` (serviço, bilhete, perna, SKU, IAP e o roteamento entre ferramentas).

A demonstração usa a linha `mg/belo horizonte - rj/rio de janeiro` em `2026-04-05`.

## O que o agente faz

A pergunta escolhe a ferramenta. O runtime valida o contrato, executa a função Python e devolve a observação. O ciclo para quando a evidência basta, quando o dado não existe, ou ao chegar a 5 iterações.

| Ferramenta | Responde |
|---|---|
| `consultar_base_de_conhecimento` | Regra de grão, definição de IAP e limite da amostra |
| `consultar_vendas` | Fato do bilhete |
| `consultar_ocupacao` | Fato da perna. A taxa de lotação não é o IAP |

O IAP é a distância transportada nos bilhetes dividida pelo ASK (assentos × quilômetro oficial). Esta amostra não tem o quilômetro oficial, então o IAP fica como pendência.

## Saída

Cada parecer concluído acrescenta uma linha em `parecer_analista.csv`, na mesma pasta do notebook.

## Mapa do notebook

| Seção | Conteúdo |
|---|---|
| 1 | Caso, grãos e glossário (bilhete, perna, ASK, IAP) |
| 2 | Ambiente, PEAS e ciclo |
| 3 | Preparação e instalação |
| 4 | Leitura dos CSVs |
| 5 | Conhecimento e recuperação |
| 6 | Três ferramentas em integração direta |
| 7 | Agente |
| 8 | Testes do runtime, sem chamar o modelo |
| 9 | Escolha do Flash e índice vetorial |
| 10 | Demonstração |
| 11 | Testes de comportamento com o modelo |
