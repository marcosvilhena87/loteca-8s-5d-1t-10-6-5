# Loteca — 8 Secos, 5 Duplos, 1 Triplo / 10-6-5

Projeto para geração e avaliação de palpites da **Loteca** com base em probabilidades históricas e otimização combinatória.

A estratégia parte das probabilidades dos três resultados possíveis de cada partida — **1**, **X** e **2** — e monta um bilhete com estrutura fixa de **8 secos, 5 duplos e 1 triplo**, totalizando **21 marcações**, distribuídas entre **10 top1, 6 top2 e 5 top3**.

O objetivo não é simplesmente concentrar as escolhas nas maiores probabilidades individuais. A proposta é usar o histórico dos concursos para decidir **onde vale a pena gastar cobertura**, combinando probabilidade, incerteza, robustez e restrições estratégicas.

---

## Estrutura do bilhete

Cada concurso possui 14 partidas.

O bilhete deve conter exatamente:

- **8 secos** → 8 marcações
- **5 duplos** → 10 marcações
- **1 triplo** → 3 marcações

Total:

```text
8 + 10 + 3 = 21 marcações
```

Essas 21 marcações devem conter exatamente:

```text
10 top1
 6 top2
 5 top3
-------
21 marcações
```

---

## Probabilidades

Para cada partida são representadas as probabilidades:

- `p(1)` — vitória do mandante
- `p(X)` — empate
- `p(2)` — vitória do visitante

As três probabilidades são ordenadas da maior para a menor para obter:

- `p(top1)` — maior probabilidade
- `p(top2)` — segunda maior probabilidade
- `p(top3)` — terceira maior probabilidade

### Desempate

Quando duas ou mais probabilidades forem iguais, a prioridade é:

```text
1 > 2 > X
```

Exemplo:

```text
p(1) = 0,38
p(X) = 0,24
p(2) = 0,38
```

Ranking:

```text
top1 = 1
top2 = 2
top3 = X
```

---

## Resultado histórico em relação ao ranking

Nos concursos já realizados, o resultado real da partida é representado por One-Hot Encoding:

- `top1_hit`
- `top2_hit`
- `top3_hit`

Exatamente uma dessas variáveis deve ser igual a `1`:

```text
top1_hit + top2_hit + top3_hit = 1
```

Isso permite estudar não apenas se o modelo acertou, mas **em qual posição do ranking probabilístico o resultado real ocorreu**.

---

## Hard Constraints

As restrições abaixo são obrigatórias e não podem ser violadas pela otimização.

### Estrutura

```text
8 secos
5 duplos
1 triplo
```

### Distribuição por ranking

```text
10 top1
6 top2
5 top3
```

### Flamengo

Quando o `FLAMENGO/RJ` participar do concurso, o resultado correspondente à sua vitória deve estar obrigatoriamente entre as marcações do bilhete.

Isso vale independentemente de a vitória do Flamengo aparecer como `top1`, `top2` ou `top3`.

---

## Soft Constraints

As preferências abaixo devem influenciar a função objetivo, mas podem ser sacrificadas quando sua aplicação causar perda relevante de qualidade global.

### Palmeiras

Favorecer soluções que **não incluam a vitória do `PALMEIRAS/SP`**, priorizando empate ou derrota quando o custo probabilístico for aceitável.

A vitória do Palmeiras não é proibida por regra rígida: ela deve receber uma penalização na função objetivo.

### Distribuição 1 / X / 2

Buscar preferencialmente:

```text
9 mandantes
6 empates
6 visitantes
```

Como são 21 marcações:

```text
9 + 6 + 6 = 21
```

Uma medida simples de desvio pode ser:

```text
D = |N1 - 9| + |NX - 6| + |N2 - 6|
```

Quanto menor `D`, melhor.

---

## Princípio de otimização

O projeto não deve escolher os 8 secos, depois os 5 duplos e depois o triplo de forma independente.

A aposta deve ser tratada como um **problema global de otimização combinatória**, porque as decisões estão interligadas:

- estrutura `8S / 5D / 1T`;
- distribuição `10 / 6 / 5` entre top1, top2 e top3;
- distribuição desejada `9 / 6 / 6` entre 1, X e 2;
- obrigação de incluir a vitória do Flamengo;
- preferência por excluir a vitória do Palmeiras;
- cobertura dos jogos mais incertos.

A meta é encontrar o melhor **bilhete completo**, e não tomar 14 decisões locais independentes.

---

## Como decidir onde usar secos, duplos e triplo

O projeto deve evitar uma estratégia baseada apenas em selecionar as maiores `p(top1)`, `p(top2)` e `p(top3)`.

Alguns critérios de maior interesse são:

### 1. Entropia do jogo

Uma medida da incerteza da partida:

```text
H = -Σ p(i) ln p(i)
```

Jogos próximos de:

```text
0,34 / 0,33 / 0,33
```

têm incerteza muito maior que jogos como:

```text
0,70 / 0,20 / 0,10
```

Os primeiros tendem a ser candidatos melhores para duplo ou triplo.

### 2. Gap top1-top2

```text
gap12 = p(top1) - p(top2)
```

Quanto menor o `gap12`, menor a vantagem do resultado mais provável sobre o segundo colocado.

### 3. Gap top2-top3

```text
gap23 = p(top2) - p(top3)
```

Quanto menor o `gap23`, maior a justificativa para considerar o terceiro resultado na cobertura.

### 4. Ganho marginal da cobertura

Em vez de perguntar apenas qual resultado possui maior probabilidade, perguntar:

> Quanto a inclusão deste resultado aumenta a chance do bilhete atingir 12+, 13+ ou 14 pontos?

Exemplo conceitual:

```text
ΔP(13+) = P(13+ | cobertura adicionada)
         - P(13+ | configuração atual)
```

Esse pode ser um critério central para escolher onde gastar os 5 duplos e o triplo.

### 5. Robustez

Uma escolha deve ser favorecida quando continua boa mesmo sob pequenas perturbações nas probabilidades estimadas.

A ideia é evitar que o bilhete dependa excessivamente de diferenças mínimas entre probabilidades muito próximas.

---

## Função objetivo

Uma formulação possível é:

```text
Score =
    w1 * P(13+)
  + w2 * P(14)
  + w3 * Robustez
  - w4 * Desvio_9_6_6
  - w5 * Penalidade_Palmeiras
```

Sujeita aos hard constraints:

```text
8 secos
5 duplos
1 triplo
10 top1
6 top2
5 top3
vitória do Flamengo incluída quando aplicável
```

Os pesos `w1...w5` devem ser avaliados por backtest e walk-forward, evitando ajustá-los apenas para maximizar o desempenho no histórico completo.

---

## Dados

### `data/concursos_anteriores.csv`

Base histórica utilizada para análise, treinamento, calibração e backtests.

Colunas atualmente disponíveis incluem:

```text
Concurso
Jogo
Mandante
Visitante
Data
1
X
2
p(1)
p(x)
p(2)
p(top1)
p(top2)
p(top3)
top1
top2
top3
```

Nos concursos concluídos, as colunas `1`, `X` e `2` representam o resultado real em formato One-Hot.

### `data/proximo_concurso.csv`

Contém as partidas e probabilidades estimadas do concurso a ser analisado.

As colunas de resultado real permanecem zeradas até a realização das partidas.

---

## Estrutura do projeto

```text
.
├── data/
│   ├── concursos_anteriores.csv
│   └── proximo_concurso.csv
│
├── models/
├── output/
│
├── scripts/
│   ├── common.py
│   ├── preprocess_data.py
│   ├── train_model.py
│   └── predict_results.py
│
└── main.py
```

### Arquitetura planejada

A evolução do projeto pode incluir:

```text
scripts/
├── common.py
├── preprocess_data.py
├── train_model.py
├── predict_results.py
├── optimize_ticket.py
├── backtest.py
└── telemetry.py
```

---

## Telemetria

A geração do bilhete deve ser auditável.

Para cada partida, o terminal deve exibir pelo menos:

```text
JOGO 03 — TIME A x TIME B

Probabilidades:
1 = 0.4012
X = 0.3041
2 = 0.2946

Ranking:
top1 = 1  (0.4012)
top2 = X  (0.3041)
top3 = 2  (0.2946)

Entropia: 1.088
gap12: 0.0971
gap23: 0.0095

Escolha: 1X
Tipo: DUPLO

Contribuição:
top1 = +1
top2 = +1
top3 = +0
```

A explicação da decisão também deve ser exibida, por exemplo:

```text
Motivos:
+ alta incerteza
+ top2 e top3 muito próximos
+ cobertura apresenta alto ganho marginal em P(13+)
+ compatível com a meta 10/6/5
```

---

## Auditoria final

Ao fim da otimização, o programa deve validar automaticamente todas as restrições.

Exemplo:

```text
=========== AUDITORIA FINAL ===========

Estrutura
[OK] 8 secos
[OK] 5 duplos
[OK] 1 triplo
[OK] 21 marcações

Ranking
[OK] top1 = 10
[OK] top2 = 6
[OK] top3 = 5

Resultados
[OK] Mandante = 9
[OK] Empate    = 6
[OK] Visitante = 6

Hard constraints
[OK] Vitória do Flamengo incluída

Soft constraints
[OK] Vitória do Palmeiras excluída
[OK] Distribuição alvo 9/6/6 atingida

Solução válida: SIM
```

---

## Avaliação histórica

O projeto deve ser validado prioritariamente por **backtest temporal / walk-forward**.

Métricas de interesse:

- média de acertos por concurso;
- frequência de 14 pontos;
- frequência de 13+ pontos;
- frequência de 12+ pontos;
- frequência de 11+ pontos;
- Brier Score;
- Log Loss;
- calibração das probabilidades;
- distribuição de `top1_hit`, `top2_hit` e `top3_hit`;
- desempenho por faixa de probabilidade;
- desempenho por nível de entropia;
- desempenho por tipo de marcação: seco, duplo e triplo.

O conjunto usado para avaliar um concurso histórico não deve utilizar informação posterior à data daquele concurso.

---

## Filosofia do projeto

As probabilidades continuam sendo a base da estratégia, mas não devem determinar mecanicamente onde ficam secos, duplos e triplo.

O foco é responder duas perguntas diferentes:

1. **Qual resultado é mais provável em cada partida?**
2. **Em qual partida uma marcação adicional produz o maior ganho para o bilhete completo?**

A segunda pergunta é o núcleo da otimização.

> Não buscar apenas as 21 maiores probabilidades. Buscar a combinação de 21 marcações que produz o melhor bilhete possível sob as restrições definidas.

---

## Status

🚧 **Em desenvolvimento.**

A estrutura de dados já está disponível no repositório. Os módulos de processamento, modelagem e otimização ainda serão implementados e validados progressivamente.
