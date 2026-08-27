# Trabalho 1 — TDD e propriedades em pipelines de ML

Disciplina: **Testes Automatizados** (Pós em IA — PUC Minas).  
**Aluno:** Andre Cardoso de Oliveira

A entrega é o notebook Colab `Trabalho1_TesteIA_Andre_Oliveira.ipynb` (`ipytest` + `hypothesis`).

## Função

`precision(y_true, y_pred)` — **precisão binária** depois da predição.

Das vezes em que o modelo disse positivo (`y_pred == 1`), quantas estavam certas (`y_true == 1`)?

```
precision = TP / (TP + FP)
```

## Os 4 elementos do enunciado

| # | Pedido | Onde está |
|---|---|---|
| 1 | TDD Red → Green → Refactor | Células do notebook **e** 1 commit por fase no Git |
| 2 | Teste de propriedade (Hypothesis) | Seção 2 do notebook |
| 3 | Propriedade pega um bug real | Seção 3: `precision_buggy` divide sem guarda (`TP + FP == 0`) |
| 4 | Decisões de design | Seção 4 do notebook (resumo abaixo) |

### Histórico Git (evidência do TDD)

Na pasta deste trabalho:

```bash
git log --oneline
```

Esperado, nesta ordem (do mais antigo ao mais novo):

1. `red: teste de precision que ainda falha`
2. `green: implementação mínima de precision`
3. `refactor: documenta e clareia precision sem mudar o comportamento`

Há commits extras depois do TDD (prova do bug, docs e cópia do `git log`). O ciclo pedido pelo enunciado são os três primeiros.

Uma cópia do log está em `evidencias_git/git_log.txt` (para envio no Canvas).

## Decisões de design

| Tópico | Decisão |
|---|---|
| **Divisão por zero** | Sem positivo previsto (`TP + FP == 0`) → `0.0`. |
| **Comprimentos diferentes** | `ValueError`. Não alinha com sentinela. |
| **Lista vazia** | Entrada inválida. Fora do domínio (`min_size=1`). |
| **Empate** | Não se aplica — não há ranking. |
| **NaN / inf** | Fora do domínio. Rótulos são `0` ou `1`, não scores. |
| **Outros inteiros** | Só `1` é classe positiva; o resto conta como negativo. |
| **String `"1"`** | Não converte. `"1" == 1` é falso. |

A propriedade (`0 <= precisão <= 1`) não escolhe entre `2/3` e `1/2`. A fórmula fica nos testes de exemplo. A divisão por zero é decisão extra: o teste Green cobre o caso, e a propriedade quebra a versão sem guarda.

## Como executar

1. Abra o Google Colab.
2. **Arquivo → Fazer upload do notebook** e escolha `Trabalho1_TesteIA_Andre_Oliveira.ipynb`.
3. Rode as células de cima para baixo.

Ordem esperada do `pytest`:

- Red: **FAILED** (`NameError` — função ainda não existe)
- Green *fake it*: **PASSED** no caso pontual
- Segundo teste com o fake: **FAILED**
- Implementação real e Refactor: **PASSED**
- Propriedade (função correta): **PASSED**
- Propriedade contra a versão bugada: **FAILED** (`ZeroDivisionError` / contraexemplo do Hypothesis)

## Estrutura

```
Trabalho1_Testes_Automatizados/
├── README.md
├── Trabalho1_TesteIA_Andre_Oliveira.ipynb
├── evidencias_git/
│   └── git_log.txt    # cópia do git log para envio no Canvas
└── .git/              # histórico TDD (enviar no zip)
```
