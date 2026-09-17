# Loteca — 8 Secos, 5 Duplos, 1 Triplo / 10-6-5

Projeto para geração, otimização e avaliação de palpites da **Loteca** com base em probabilidades históricas e otimização combinatória.

A estratégia parte das probabilidades dos três resultados possíveis de cada partida — **1**, **X** e **2** — e monta um bilhete com estrutura fixa de **8 secos, 5 duplos e 1 triplo**, totalizando **21 marcações**, distribuídas entre **10 top1, 6 top2 e 5 top3**.

O objetivo não é simplesmente concentrar as escolhas nas maiores probabilidades individuais. A proposta é decidir **onde vale a pena gastar cobertura**, combinando probabilidade, incerteza, restrições estruturais, padrões históricos e preferências estratégicas.

---

## Objetivo

Gerar um palpite alinhado aos constraints do projeto, utilizando `data/concursos_anteriores.csv` como base histórica para análise, treinamento, calibração e validação.

O projeto deve responder duas perguntas diferentes:

1. **Qual resultado é mais provável em cada partida?**
2. **Em qual partida uma marcação adicional produz o maior ganho para o bilhete completo?**

A segunda pergunta é o núcleo da otimização.

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

### 1. Estrutura

```text
8 secos
5 duplos
1 triplo
```

### 2. Distribuição por ranking

```text
10 top1
6 top2
5 top3
```

### 3. Flamengo

Quando o `FLAMENGO/RJ` participar do concurso, o resultado correspondente à sua vitória deve estar obrigatoriamente entre as marcações do bilhete.

Isso vale independentemente de a vitória do Flamengo aparecer como `top1`, `top2` ou `top3`.

---

## Soft Constraints

As preferências abaixo influenciam a função objetivo, mas podem ser sacrificadas quando sua aplicação causar perda relevante de qualidade global.

### 1. Palmeiras

Favorecer soluções que **não incluam a vitória do `PALMEIRAS/SP`**, priorizando empate ou derrota quando o custo probabilístico for aceitável.

A vitória do Palmeiras não é proibida por regra rígida: deve ser tratada como preferência e auditada pelo seu custo de oportunidade.

### 2. Distribuição 1 / X / 2

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

Uma medida simples de desvio é:

```text
D = |N1 - 9| + |NX - 6| + |N2 - 6|
```

Quanto menor `D`, melhor.

### 3. Dispersão dos top1

Favorecer soluções em que os `top1` selecionados **não formem sequências excessivamente longas** quando os 14 jogos são ordenados por `p(top1)` da maior para a menor.

A finalidade é reduzir concentração estrutural sem abandonar top1 muito fortes apenas por estética combinatória.

Exemplo:

```text
Jogos ordenados por p(top1):
J05 J01 J02 J07 J09 J08 J12 J11 J14 J04 J03 J13 J10 J06

Top1 presente no bilhete:
 1   1   1   1   0   1   1   1   0   1   0   1   0   1

Runs:
4 / 3 / 1 / 1 / 1
```

Uma penalidade candidata é:

```text
Penalty_run = Σ max(0, Lr - L0)^2
```

onde:

- `Lr` = comprimento de cada sequência consecutiva de top1;
- `L0` = comprimento tolerado sem penalização.

O valor de `L0` não deve ser escolhido apenas por intuição. Preferencialmente deve ser estimado a partir da distribuição histórica observada em `data/concursos_anteriores.csv`.

#### Custo da quebra

Quando for útil quebrar uma sequência longa, a preferência deve recair sobre jogos em que o custo probabilístico seja baixo.

Uma aproximação simples é:

```text
custo_quebra(j) = p(top1)_j - p(top2)_j
```

Ou seja, quanto menor o `gap12`, mais barato é deixar de concentrar a aposta no top1 daquele jogo.

A regra desejada é:

> evitar concentração de top1 quando a quebra dessa concentração custa pouco em probabilidade.

---

## Princípio de otimização

O projeto não escolhe os 8 secos, depois os 5 duplos e depois o triplo de forma independente.

A aposta é tratada como um **problema global de otimização combinatória**, porque as decisões estão interligadas:

- estrutura `8S / 5D / 1T`;
- distribuição `10 / 6 / 5` entre top1, top2 e top3;
- distribuição desejada `9 / 6 / 6` entre 1, X e 2;
- obrigação de incluir a vitória do Flamengo;
- preferência por excluir a vitória do Palmeiras;
- dispersão das marcações top1;
- cobertura dos jogos mais incertos.

A meta é encontrar o melhor **bilhete completo**, e não tomar 14 decisões locais independentes.

---

## Como decidir onde usar secos, duplos e triplo

O projeto evita uma estratégia baseada apenas em selecionar as maiores `p(top1)`, `p(top2)` e `p(top3)`.

### Entropia do jogo

```text
H = -Σ p(i) ln p(i)
```

Jogos próximos de `0,34 / 0,33 / 0,33` têm incerteza muito maior que jogos como `0,70 / 0,20 / 0,10`.

### Gap top1-top2

```text
gap12 = p(top1) - p(top2)
```

Quanto menor o `gap12`, menor a vantagem do resultado mais provável sobre o segundo colocado.

### Gap top2-top3

```text
gap23 = p(top2) - p(top3)
```

Quanto menor o `gap23`, maior a proximidade entre a segunda e a terceira alternativas.

### Cobertura da seleção

```text
Cobertura = Σ p(resultado selecionado)
```

Exemplos:

```text
Seco 1: cobertura = p(1)
Duplo 1X: cobertura = p(1) + p(X)
Triplo 1X2: cobertura = 1
```

### Ganho marginal da cobertura

Uma evolução planejada é avaliar diretamente:

```text
ΔP(13+) = P(13+ | cobertura adicionada)
         - P(13+ | configuração anterior)
```

A pergunta deixa de ser apenas "qual resultado tem maior probabilidade?" e passa a incluir "em qual jogo uma marcação adicional compra mais probabilidade de 13+ ou 14 pontos?".

---

## Probabilidade do bilhete

O projeto já calcula exatamente, sem Monte Carlo, a distribuição de acertos do bilhete a partir da cobertura de cada partida.

São calculadas atualmente:

```text
P(14)
P(13+)
P(12+)
```

A implementação usa programação dinâmica sobre as probabilidades de acerto de cada jogo.

Uma evolução natural é exibir também:

```text
E[acertos]
P(11+)
P(10+)
moda da distribuição
desvio-padrão
```

### Valor da cobertura

Uma métrica planejada é:

```text
VC(j) = ΔP(13+) / marcações adicionais
```

Ela mede quanto de probabilidade adicional de premiação cada marcação extra compra.

---

## Função objetivo atual

O otimizador atual usa uma função aditiva para permitir programação dinâmica eficiente.

Por seleção, a contribuição principal é aproximadamente:

```text
log(cobertura)
+ bônus de entropia para duplos/triplos
- penalidade pela vitória do Palmeiras
```

Ao final, também é aplicada penalização pelo desvio em relação à meta `9/6/6`.

Portanto:

> **P(13+), P(14) e P(12+) são calculadas exatamente para avaliar o bilhete, mas o otimizador ainda não maximiza diretamente essas probabilidades.**

Entre as evoluções prioritárias estão:

- otimização orientada diretamente a `P(13+)`;
- custo de oportunidade dos soft constraints;
- penalidade histórica para runs de top1;
- robustez a pequenas perturbações nas probabilidades.

---

## Dados

### `data/concursos_anteriores.csv`

Base histórica utilizada para análise, treinamento, calibração e backtests.

Colunas disponíveis incluem:

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

## Análise histórica das sequências de top1

Uma implementação planejada é transformar cada concurso histórico em uma sequência binária após ordenar os jogos por `p(top1)` decrescente.

Exemplo:

```text
1 1 0 1 1 1 0 0 1 0 1 0 0 1
```

A partir dela podem ser calculadas:

```text
max_run
mean_run
n_runs
run_concentration = Σ Lr²
```

Também deve ser comparada a sequência de:

1. **top1 presente no bilhete**;
2. **seco em top1**.

Esses dois fenômenos não são equivalentes e devem ser avaliados separadamente no backtest.

A regra de dispersão só deve ser mantida se apresentar ganho fora da amostra ou funcionar como regularização útil sem custo relevante em probabilidade.

---

## Telemetria

Para cada partida, o terminal deve exibir pelo menos:

```text
JOGO 03 — TIME A x TIME B
Probabilidades: 1=0.4012 X=0.3041 2=0.2946
Ranking: top1=1 top2=X top3=2
Entropia=1.088 gap12=0.0971 gap23=0.0095
Escolha=X2 Tipo=DUPLO Cobertura=0.5988
```

Ao final:

```text
=========== AUDITORIA FINAL ===========
[OK] 8 secos, 5 duplos, 1 triplo, 21 marcações
[OK] top1=10, top2=6, top3=5
[OK/INFO] 1/X/2=... (alvo 9/6/6)
[OK] Vitória do Flamengo incluída quando aplicável
[OK/INFO] Vitória do Palmeiras excluída ou incluída com penalização
P(14)=...
P(13+)=...
P(12+)=...
Solução válida: SIM
```

### Telemetria planejada para dispersão top1

```text
=========== DISTRIBUIÇÃO TOP1 ===========

Jogos ordenados por p(top1):
05 01 02 07 09 08 12 11 14 04 03 13 10 06

Top1 presente:
 1  1  1  1  0  1  1  1  0  1  0  1  0  1

Runs: 4 / 3 / 1 / 1 / 1
Maior sequência: 4
Média das sequências: 2.00
Concentração: 28
Penalidade de run: ...
```

Quando disponível, a telemetria também deve comparar o bilhete com o histórico:

```text
mediana histórica max_run = ...
P(max_run >= atual) = ...
```

---

## Análise marginal

A telemetria deve evoluir para mostrar não apenas qual solução venceu, mas também quanto custariam as alternativas.

Exemplo:

```text
JOGO 06 — REMO x SANTOS
Atual: 1X
P(13+) atual = 1.163062%

Alternativa 12:
P(13+) = 1.171800%
Δ = +0.008738 p.p.

Motivo de não selecionar:
- violaria a distribuição 10/6/5
```

O mesmo princípio deve ser aplicado ao triplo, à preferência contra o Palmeiras, à meta `9/6/6` e à quebra de runs de top1.

---

## Custo de oportunidade dos soft constraints

As preferências devem se tornar auditáveis em termos de perda real de probabilidade.

```text
Melhor solução sem preferência:
P(13+) = 1.1820%

Melhor solução com preferência:
P(13+) = 1.1630%

Custo absoluto = -0.0190 p.p.
Custo relativo = -1.61%
```

Fórmula:

```text
custo_relativo =
(P13_otimo - P13_alternativo) / P13_otimo
```

Isso permitirá substituir penalizações arbitrárias por regras condicionadas ao custo real.

---

## Validação histórica

A validação deve ser feita prioritariamente por **backtest temporal / walk-forward**.

Para cada concurso histórico:

1. usar somente dados disponíveis antes daquele concurso;
2. estimar `p(1)`, `p(X)` e `p(2)`;
3. gerar o bilhete;
4. confrontar com os resultados reais;
5. registrar métricas.

Nenhuma informação posterior ao concurso avaliado pode participar do treinamento ou da calibração.

### Métricas de interesse

- média de acertos;
- frequência de 14 pontos;
- frequência de 13+;
- frequência de 12+;
- frequência de 11+;
- `P(14)` prevista;
- `P(13+)` prevista;
- Brier Score;
- Log Loss;
- ECE / calibração;
- frequência de `top1_hit`, `top2_hit`, `top3_hit`;
- desempenho por faixa de probabilidade;
- desempenho por entropia;
- desempenho por tipo de marcação;
- custo dos soft constraints;
- distribuição histórica de `max_run`, `mean_run` e `n_runs`;
- desempenho com e sem penalidade de sequência top1.

---

## Calibração das probabilidades

Antes de otimizar o bilhete, é importante verificar se as probabilidades são calibradas.

Métricas e técnicas candidatas:

```text
Brier Score
Log Loss
ECE
Reliability bins
Isotonic Regression
Platt Scaling
Temperature Scaling
```

O objetivo é evitar otimizar agressivamente probabilidades mal calibradas.

---

## Arquitetura

Estrutura atual:

```text
.
├── data/
│   ├── concursos_anteriores.csv
│   └── proximo_concurso.csv
├── models/
├── output/
├── scripts/
│   ├── common.py
│   ├── constraints.py
│   ├── metrics.py
│   ├── preprocess_data.py
│   ├── train_model.py
│   ├── predict_results.py
│   └── optimize_ticket.py
└── main.py
```

Arquitetura planejada:

```text
scripts/
├── common.py
├── preprocess_data.py
├── train_model.py
├── predict_results.py
├── optimize_ticket.py
├── probability_metrics.py
├── historical_patterns.py
├── constraints.py
├── telemetry.py
├── backtest.py
├── calibration.py
└── validate_ticket.py
```

Responsabilidades:

- **modelo** → estima probabilidades;
- **otimizador** → monta o bilhete;
- **probability_metrics** → calcula distribuição de acertos e métricas probabilísticas;
- **historical_patterns** → mede runs, concentração e padrões históricos;
- **constraints** → centraliza hard e soft constraints;
- **telemetria** → explica decisões;
- **backtest** → mede desempenho histórico sem vazamento temporal;
- **validador** → verifica independentemente a integridade do bilhete.

---

## Execução

Para gerar o bilhete do próximo concurso:

```bash
python main.py
```

Por padrão:

```text
Entrada: data/proximo_concurso.csv
Saída:   output/ticket.csv
```

Também é possível informar outro arquivo:

```bash
python main.py caminho/do/concurso.csv --output caminho/do/bilhete.csv
```

---

## Roadmap

### Implementado

- leitura das probabilidades `1/X/2`;
- ranking `top1/top2/top3`;
- desempate `1 > 2 > X`;
- otimização global por programação dinâmica;
- hard constraints `8/5/1` e `10/6/5`;
- vitória do Flamengo obrigatória;
- preferência `9/6/6`;
- penalização da vitória do Palmeiras;
- entropia e gaps;
- cálculo exato de `P(14)`, `P(13+)` e `P(12+)`;
- auditoria final;
- exportação do bilhete.

### Próximas prioridades

1. estatísticas históricas das sequências de `top1_hit`;
2. telemetria de `max_run`, `mean_run`, `n_runs` e concentração;
3. penalidade suave de runs baseada no histórico;
4. custo probabilístico para quebrar uma sequência;
5. análise marginal de secos, duplos e triplo;
6. custo de oportunidade dos soft constraints;
7. backtest walk-forward comparando estratégias com e sem dispersão top1;
8. otimização orientada diretamente a `P(13+)`.

### Evoluções posteriores

- calibração das probabilidades;
- robustez a perturbações;
- múltiplas soluções quase ótimas;
- configuração externa por `config.yaml`;
- testes unitários e de integração;
- validador independente;
- comparação de múltiplos objetivos: `P(12+)`, `P(13+)`, `P(14)`.

---

## Filosofia do projeto

As probabilidades continuam sendo a base da estratégia, mas não devem determinar mecanicamente onde ficam secos, duplos e triplo.

O projeto deve evitar dois extremos:

1. selecionar simplesmente as 21 maiores probabilidades;
2. diversificar apenas para produzir um bilhete visualmente equilibrado.

A diversificação só deve entrar quando houver justificativa histórica, ganho de robustez ou baixo custo de oportunidade.

> **Não buscar apenas as 21 maiores probabilidades. Buscar a combinação de 21 marcações que produz o melhor bilhete possível sob as restrições definidas.**

---

## Status

🚧 **Em desenvolvimento.**

O otimizador global já gera bilhetes válidos e auditáveis. As próximas etapas concentram-se em validar empiricamente os soft constraints, ampliar a telemetria e aproximar a função objetivo das probabilidades reais de premiação.