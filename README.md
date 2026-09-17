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

O projeto calcula exatamente, sem Monte Carlo, a distribuição de acertos do bilhete a partir da cobertura de cada partida.

São calculadas atualmente:

```text
P(14)
P(13+)
P(12+)
P(11+)
P(10+)
E[acertos]
moda da distribuição
desvio-padrão
```

A implementação usa programação dinâmica sobre as probabilidades de acerto de cada jogo.

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

---

## Próxima arquitetura de otimização: DP Top-N + reranqueamento exato

A principal evolução planejada é deixar de manter apenas **um** candidato por estado da programação dinâmica.

Em vez disso, cada estado poderá preservar os melhores `N` candidatos segundo o score aditivo intermediário:

```text
N = 20
N = 50
N = 100
```

Ao final, todos os candidatos válidos serão reranqueados usando métricas globais calculadas exatamente:

```text
P(14)
P(13+)
P(12+)
P(11+)
E[acertos]
max_run
concentração de top1
custo dos soft constraints
```

A ideia é evitar que um bilhete com ótimo `P(13+)` seja descartado cedo apenas porque teve score local ligeiramente inferior durante a DP.

### Fluxo desejado

```text
1. DP gera candidatos válidos
2. Cada estado preserva Top-N soluções
3. Hard constraints continuam invioláveis
4. Finalistas recebem métricas globais exatas
5. Finalistas são reranqueados pela função objetivo real
6. O melhor bilhete e alternativas quase ótimas são exibidos
```

Essa abordagem mantém boa eficiência computacional e aproxima o projeto da otimização direta das métricas realmente importantes.

---

## Comparação de objetivos

O projeto deve permitir comparar diferentes objetivos para o mesmo concurso.

Exemplos:

```text
--objective p14
--objective p13plus
--objective p12plus
--objective balanced
```

Uma formulação balanceada possível é:

```text
Score =
    w12 * P(12+)
  + w13 * P(13+)
  + w14 * P(14)
  - penalidades_soft
```

A telemetria deve mostrar os trade-offs entre os objetivos.

Exemplo:

```text
Estratégia     P(14)      P(13+)     P(12+)
p14            0.121%     1.12%      5.31%
p13plus        0.114%     1.18%      5.58%
balanced       0.117%     1.16%      5.62%
```

---

## Soft constraints por custo máximo

Uma evolução importante é substituir pesos arbitrários por regras baseadas em custo de oportunidade.

Exemplo para o Palmeiras:

```text
Aplicar preferência de excluir vitória do Palmeiras
somente se o custo relativo em P(13+) <= 2%
```

O mesmo princípio pode ser aplicado a:

- meta `9/6/6`;
- limite de `max_run`;
- concentração de top1;
- outras preferências estratégicas.

Fórmula:

```text
custo_relativo =
(P13_otimo - P13_alternativo) / P13_otimo
```

---

## Custo de diversificação

A dispersão dos top1 deve ser tratada como um trade-off mensurável.

O projeto deve comparar automaticamente variantes como:

```text
sem limite de max_run
max_run <= 7
max_run <= 6
max_run <= 5
```

Para cada cenário, exibir:

```text
P(14)
P(13+)
P(12+)
max_run
concentração
custo absoluto
custo relativo
```

Isso permite decidir se a diversificação é barata ou se destrói qualidade probabilística.

---

## Baseline correto para concentração de top1

A concentração estrutural do bilhete e o padrão histórico de `top1_hit` são fenômenos diferentes.

### Estrutura do bilhete

O bilhete possui obrigatoriamente exatamente **10 top1 em 14 posições**.

Portanto, `max_run`, `mean_run`, `n_runs` e concentração devem ser comparados com um baseline combinatório condicionado a exatamente 10 marcações top1.

### Histórico dos resultados

Os concursos históricos devem analisar separadamente a sequência de `top1_hit`, cuja quantidade varia livremente de concurso para concurso.

A telemetria deve evitar comparar diretamente essas duas distribuições.

---

## Análise histórica das sequências de top1

Para cada concurso histórico, os jogos podem ser ordenados por `p(top1)` decrescente e transformados em sequências binárias.

Podem ser calculadas:

```text
max_run
mean_run
n_runs
run_concentration = Σ Lr²
```

Também devem ser analisados separadamente:

1. **top1 presente no bilhete**;
2. **seco em top1**;
3. **top1_hit histórico**.

A regra de dispersão só deve ser mantida se demonstrar utilidade fora da amostra ou regularização útil com baixo custo probabilístico.

---

## Análise marginal e contrafactual

A telemetria deve mostrar não apenas qual solução venceu, mas também quanto custariam as alternativas.

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

O mesmo princípio deve ser aplicado a:

- posição do triplo;
- cada duplo;
- exclusão do Palmeiras;
- meta `9/6/6`;
- quebra de sequências de top1.

---

## Classificação do motivo de cada decisão

Cada escolha deve poder informar seu motivo predominante.

Exemplo:

```text
J01 — seco 1
Motivo principal: probabilidade muito alta
Hard constraint Flamengo: SIM

J13 — triplo 1X2
Motivo principal: alta incerteza
Entropia: alta
Influência 10/6/5: moderada
```

Isso torna a telemetria mais explicativa e ajuda a identificar quando uma marcação foi escolhida pela probabilidade ou apenas para fechar constraints.

---

## Múltiplas soluções quase ótimas

O sistema não deve retornar apenas um único bilhete quando existirem alternativas estatisticamente próximas.

Exemplo:

```text
#1 P(13+) = 1.1631%
#2 P(13+) = 1.1618%
#3 P(13+) = 1.1609%
```

Isso permite preferir uma solução ligeiramente inferior em probabilidade quando ela apresenta vantagens relevantes em robustez ou soft constraints.

---

## Fronteira de Pareto

Uma evolução posterior é identificar bilhetes não dominados considerando simultaneamente:

```text
P(14)
P(13+)
P(12+)
concentração de top1
soft constraints
robustez
```

Exemplo:

```text
A — maior P(13+)
B — -0,4% relativo em P(13+), mas max_run cai de 9 para 5
C — -0,8%, exclui Palmeiras e mantém 9/6/6
```

A fronteira de Pareto evita comprimir todas as preferências em um único peso arbitrário.

---

## Robustez das probabilidades

O bilhete não deve depender excessivamente de diferenças mínimas entre probabilidades.

Uma análise planejada é perturbar `p(1)`, `p(X)` e `p(2)` dentro de margens plausíveis e regenerar o bilhete.

Para cada jogo, registrar:

```text
frequência de cada marcação
estabilidade do seco
estabilidade dos duplos
estabilidade do triplo
```

Exemplo:

```text
J01 — 99% das perturbações mantêm 1
J06 — 54% usam 1X, 31% usam 12, 15% usam X2
```

Esse indicador ajuda a distinguir escolhas sólidas de decisões marginais.

---

## Ablation tests dos soft constraints

Cada soft constraint deve provar seu valor fora da amostra.

O backtest deve comparar incrementalmente:

```text
baseline
+ entropia
+ preferência Palmeiras
+ meta 9/6/6
+ dispersão de top1
+ robustez
```

Também deve rodar versões removendo uma regra por vez.

Métricas de comparação:

```text
média de acertos
P(12+) realizada
P(13+) realizada
frequência de 12+
frequência de 13+
frequência de 14
```

Se um soft constraint não produzir ganho consistente fora da amostra, seu peso deve ser reduzido ou zerado.

---

## Validação histórica / walk-forward

Para cada concurso histórico:

1. usar somente dados disponíveis antes daquele concurso;
2. estimar `p(1)`, `p(X)` e `p(2)`;
3. gerar o bilhete;
4. confrontar com os resultados reais;
5. registrar métricas.

Nenhuma informação posterior ao concurso avaliado pode participar do treinamento ou da calibração.

Métricas de interesse:

```text
média de acertos
frequência de 14
frequência de 13+
frequência de 12+
frequência de 11+
Brier Score
Log Loss
ECE
calibração por faixa
custo dos soft constraints
estabilidade
```

---

## Calibração e erro condicional

As probabilidades devem ser avaliadas por faixa e por tipo de resultado.

Exemplos:

```text
top1 35–40%
top1 40–50%
top1 50–60%
top1 >60%
```

Também devem ser estudadas relações condicionais como:

```text
P(top2_hit | gap12 < 0.05)
P(top3_hit | entropia > 1.08)
```

Isso pode fornecer critérios históricos mais sólidos para alocar duplos e triplo.

---

## Configuração e reprodutibilidade

Pesos, limiares e preferências devem migrar gradualmente para um arquivo como `config.yaml`.

Exemplo:

```yaml
hard:
  secos: 8
  duplos: 5
  triplos: 1
  top1: 10
  top2: 6
  top3: 5

soft:
  target_outcomes: [9, 6, 6]
  avoid_palmeiras: true
  max_cost_palmeiras: 0.02
  max_run_target: 6

optimizer:
  top_n_per_state: 50
  objective: p13plus
```

Cada bilhete salvo deve registrar metadados suficientes para reprodução:

```text
strategy_version
config_hash
input_hash
timestamp
```

---

## Validador independente e testes invariantes

Além do validador do otimizador, é desejável um módulo independente que confirme:

```text
14 jogos
21 marcações
8/5/1
10/6/5
Flamengo incluído quando aplicável
probabilidades válidas
```

Também devem ser testadas invariantes probabilísticas:

```text
0 <= p(i) <= 1
p(1) + p(X) + p(2) = 1
P(14) <= P(13+) <= P(12+) <= P(11+) <= P(10+)
```

Casos especiais de teste:

- empates de probabilidade e desempate `1 > 2 > X`;
- Flamengo mandante e visitante;
- Palmeiras mandante e visitante;
- leitura de decimal com vírgula;
- concurso sem solução válida;
- probabilidades inválidas.

---

## Estrutura planejada do projeto

```text
scripts/
├── common.py
├── preprocess_data.py
├── train_model.py
├── predict_results.py
├── optimize_ticket.py
├── metrics.py
├── constraints.py
├── historical_patterns.py
├── telemetry.py
├── robustness.py
├── backtest.py
├── calibration.py
└── validate_ticket.py
```

Separação desejada:

- **modelo** → estima probabilidades;
- **otimizador** → gera candidatos e monta o bilhete;
- **métricas** → calcula distribuição de acertos e métricas probabilísticas;
- **constraints** → centraliza hard e soft constraints;
- **historical_patterns** → analisa runs, concentração e padrões históricos;
- **telemetria** → explica decisões e contrafactuais;
- **robustez** → mede estabilidade a perturbações;
- **backtest** → valida a estratégia temporalmente;
- **calibration** → calibra probabilidades;
- **validate_ticket** → auditoria independente.

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
=========== DISTRIBUIÇÃO TOP1 ===========
Jogos ordenados por p(top1): ...
Top1 presente: ...
Runs: ...
Maior sequência: ...
Média das sequências: ...
Número de sequências: ...
Concentração: ...

=========== AUDITORIA FINAL ===========
[OK] 8 secos, 5 duplos, 1 triplo, 21 marcações
[OK] top1=10, top2=6, top3=5
[OK/INFO] 1/X/2=... (alvo 9/6/6)
[OK] Vitória do Flamengo incluída quando aplicável
[OK/INFO] Vitória do Palmeiras excluída ou incluída com penalização
P(14)=...
P(13+)=...
P(12+)=...
E[acertos]=...
Desvio-padrão=...
Moda=...
P(11+)=...
P(10+)=...
Solução válida: SIM
```

---

## Roadmap priorizado

### Implementado

- leitura das probabilidades `p(1)`, `p(X)`, `p(2)`;
- ranking `top1/top2/top3` com desempate `1 > 2 > X`;
- hard constraints `8/5/1` e `10/6/5`;
- obrigatoriedade da vitória do Flamengo;
- soft constraints de Palmeiras e `9/6/6`;
- otimização global por programação dinâmica;
- cálculo exato de `P(14)`, `P(13+)`, `P(12+)`, `P(11+)` e `P(10+)`;
- `E[acertos]`, moda e desvio-padrão;
- telemetria de entropia, gaps e cobertura;
- análise de runs e concentração dos top1;
- auditoria automática do bilhete.

### Próximas prioridades

1. **DP Top-N + reranqueamento exato**;
2. comparação de objetivos `p14`, `p13plus`, `p12plus` e `balanced`;
3. custo de oportunidade dos soft constraints;
4. custo de diversificação por `max_run`;
5. análise marginal / contrafactual;
6. múltiplas soluções quase ótimas;
7. baseline combinatório correto para concentração de top1;
8. backtest walk-forward;
9. ablation tests.

### Evoluções posteriores

- robustez a perturbações;
- estabilidade por jogo;
- fronteira de Pareto;
- calibração avançada;
- análise de erro condicional;
- `config.yaml`;
- versionamento e reprodutibilidade;
- suíte completa de testes automatizados.

---

## Filosofia do projeto

As probabilidades continuam sendo a base da estratégia, mas não devem determinar mecanicamente onde ficam secos, duplos e triplo.

O foco é encontrar a combinação de 21 marcações que produza o melhor bilhete possível sob as restrições definidas, mensurando explicitamente o custo das preferências e evitando confundir regularização útil com padrões estéticos.

> Não buscar apenas as 21 maiores probabilidades. Buscar o melhor compromisso entre probabilidade, cobertura, estrutura, robustez e constraints — e conseguir explicar por que o bilhete escolhido venceu as alternativas.

---

## Status

🚧 **Em desenvolvimento ativo.**

O projeto já gera bilhetes válidos, calcula a distribuição probabilística de acertos e fornece telemetria suficiente para auditoria estrutural. A principal próxima evolução é ampliar a busca com **DP Top-N + reranqueamento exato**, permitindo escolher o bilhete final pelas métricas globais que realmente importam.