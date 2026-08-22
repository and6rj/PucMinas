# Trabalho 1 — TDD e propriedades em pipelines de ML

Disciplina: **Testes Automatizados** (Pós em IA — PUC Minas).  
Este repositório documenta e implementa o Trabalho 1. A evidência do TDD é o histórico de commits (`red` / `green` / `refactor`).

## Enunciado

Implementar uma função Python relacionada a **pipelines de ML**. Exemplos aceitos:

- validação de score
- normalização de lote
- deduplicação de dados
- seleção de classe
- detecção de outliers
- outra função equivalente

A entrega deve demonstrar, de forma visível, **quatro elementos**:

### 1. Ciclo TDD completo (Red → Green → Refactor)

Evidenciado por **uma** das opções:

- histórico de commits no Git, com **1 commit por fase** (`red` / `green` / `refactor`);
- relato escrito passo a passo, mostrando o teste falhando, o código mínimo que faz passar e o refactor final.

### 2. Pelo menos 1 teste de propriedade (invariante)

De preferência com a biblioteca **Hypothesis**, testando um comportamento que vale para **qualquer entrada válida** — não apenas um exemplo pontual.

### 3. Prova de que a propriedade pega um bug real

Criar uma versão propositalmente **bugada** da função e mostrar que o teste de propriedade **falha** contra ela (ou seja, o teste realmente teria pego o bug em produção).

### 4. Documentação breve das decisões de design

Registrar como tratar casos de borda aplicáveis à função escolhida, por exemplo: `NaN`, `inf`, divisão por zero, empates, etc.

## Função escolhida

`minmax_transform(scores, feature_min, feature_max)` — normalização min-max de um lote usando **estatísticas congeladas do treino**.

Não calcula min/max no lote da hora (antipadrão de *train/serve skew* da Aula 2). O mesmo score, com os mesmos stats, sempre cai no mesmo valor — em treino e em serving.

## Status

- [x] Escolher a função do pipeline de ML
- [x] Red — teste que falha
- [ ] Green — implementação mínima que faz o teste passar
- [ ] Refactor — código limpo sem mudar o comportamento
- [ ] Teste de propriedade (Hypothesis)
- [ ] Versão bugada + evidência de que a propriedade falha
- [ ] Documentar decisões de design neste README

## Estrutura prevista

```
Trabalho1_Testes_Automatizados/
├── README.md
├── pytest.ini
├── requirements.txt
├── src/
│   ├── __init__.py
│   └── minmax_transform.py
└── tests/
    └── test_minmax_transform.py
```

## Decisões de design

Serão preenchidas após a escolha da função. Itens a cobrir, quando aplicáveis:

- `NaN` e `inf`
- divisão por zero / lote vazio
- empates (ex.: duas classes com o mesmo score)
- tipos e faixas de entrada aceitos
- o que a função retorna em caso de entrada inválida (exceção vs. valor sentinela)

## Como executar (a preencher)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

## Referências

- Aula 01 — testes unitários, integração e regressão
- Aula 02 — TDD aplicado a ML e testes baseados em propriedades
- [Hypothesis](https://hypothesis.readthedocs.io/)
