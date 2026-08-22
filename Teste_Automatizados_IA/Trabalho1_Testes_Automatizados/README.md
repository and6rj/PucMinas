# Trabalho 1 — TDD e propriedades em pipelines de ML

Disciplina: **Testes Automatizados** (Pós em IA — PUC Minas).  
**Aluno:** Andre Cardoso de Oliveira

A entrega é o notebook Colab `Trabalho1_TesteIA_Andre_Oliveira.ipynb`, no mesmo formato das aulas (`ipytest` + `hypothesis`).

## Função

`most_confident_class(scores)` — **seleção de classe** depois de um `softmax`.

Recebe uma lista de scores (um por classe) e devolve o **índice** do maior valor (`argmax`).

## Os 4 elementos do enunciado

| # | Pedido | Onde está |
|---|---|---|
| 1 | TDD Red → Green → Refactor | Células do notebook + 1 commit por fase no Git |
| 2 | Teste de propriedade (Hypothesis) | Seção 2 do notebook |
| 3 | Propriedade pega um bug real | Seção 3: `most_confident_class_buggy` sempre devolve `0` |
| 4 | Decisões de design | Seção 4 do notebook (resumo abaixo) |

### Histórico Git (evidência do TDD)

Na pasta deste trabalho:

```bash
git log --oneline
```

Esperado, nesta ordem (do mais antigo ao mais novo):

1. `red: teste de most_confident_class que ainda falha`
2. `green: implementação mínima de most_confident_class`
3. `refactor: documenta e clareia most_confident_class sem mudar o comportamento`

Há commits extras depois do TDD (prova do bug e, se houver, docs). O ciclo pedido pelo enunciado são os três primeiros.

## Decisões de design

| Tópico | Decisão |
|---|---|
| **Empate** | Menor índice (primeira ocorrência). `list.index(max(scores))`. |
| **Lista vazia** | Entrada inválida. Fora do domínio (`min_size=1`). |
| **NaN** | Score inválido. Fora da propriedade (`allow_nan=False`). Validar é etapa anterior ao `argmax`. |
| **inf / -inf** | Score inválido (`allow_infinity=False`). |
| **Divisão por zero** | Não se aplica — a função não divide. |
| **Tipos** | Lista de `float`. Não converte `bool` nem string. |
| **Entrada inválida** | Sem sentinela e sem “conserto” silencioso. O contrato é lista não vazia de scores finitos. |

A propriedade (`scores[idx] == max(scores)`) não escolhe entre dois máximos iguais. O menor índice é decisão extra, coberta pelo teste de exemplo do Green.

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
- Propriedade contra a versão bugada: **FAILED** (contraexemplo do Hypothesis)

## Estrutura

```
Trabalho1_Testes_Automatizados/
├── README.md
├── Trabalho1_TesteIA_Andre_Oliveira.ipynb
├── evidencias_git/
│   └── git_log.txt    # cópia do git log para envio no Canvas
└── .git/              # histórico original (enviar no zip)
```

## Referências

- Aula 01 — testes unitários, integração e regressão
- Aula 02 — TDD aplicado a ML e testes baseados em propriedades
- [Hypothesis](https://hypothesis.readthedocs.io/)
