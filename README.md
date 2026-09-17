# Loteca — 8 Secos, 5 Duplos, 1 Triplo / 10-6-5

Projeto para geração, otimização e avaliação de palpites da **Loteca** com base em probabilidades históricas e otimização combinatória.

A estratégia parte das probabilidades dos três resultados possíveis de cada partida — **1**, **X** e **2** — e monta um bilhete com estrutura fixa de **8 secos, 5 duplos e 1 triplo**, totalizando **21 marcações**, distribuídas entre **10 top1, 6 top2 e 5 top3**.

O objetivo não é simplesmente concentrar as escolhas nas maiores probabilidades individuais. A proposta é decidir **onde vale a pena gastar cobertura**, combinando probabilidade, incerteza, restrições estruturais e preferências estratégicas.

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

As preferências abaixo influenciam a função objetivo, mas podem ser sacrificadas quando sua aplicação causar perda relevante de qualidade global.

### Palmeiras

Favorecer soluções que **não incluam a vitória do `PALMEIRAS/SP`**, priorizando empate ou derrota quando o custo probabilístico for aceitável.

A vitória do Palmeiras não é proibida por regra rígida: atualmente ela recebe penalização na função objetivo.

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

Uma medida simples de desvio é:

```text
D = |N1 - 9| + |NX - 6| + |N2 - 6|
```

Quanto menor `D`, melhor.

---

## Princípio de otimização

O projeto não escolhe os 8 secos, depois os 5 duplos e depois o triplo de forma independente.

A aposta é tratada como um **problema global de otimização combinatória**, porque as decisões estão interligadas:

- estrutura `8S / 5D / 1T`;
- distribuição `10 / 6 / 5` entre top1, top2 e top3;
- distribuição desejada `9 / 6 / 6` entre 1, X e 2;
- obrigação de incluir a vitória do Flamengo;
- preferência por excluir a vitória do Palmeiras;
- cobertura dos jogos mais incertos.

A meta é encontrar o melhor **bilhete completo**, e não tomar 14 decisões locais independentes.

---

## Como decidir onde usar secos, duplos e triplo

O projeto evita uma estratégia baseada apenas em selecionar as maiores `p(top1)`, `p(top2)` e `p(top3)`.

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

### 2. Gap top1-top2

```text
gap12 = p(top1) - p(top2)
```

Quanto menor o `gap12`, menor a vantagem do resultado mais provável sobre o segundo colocado.

### 3. Gap top2-top3

```text
gap23 = p(top2) - p(top3)
```

Quanto menor o `gap23`, maior a proximidade entre a segunda e a terceira alternativas.

### 4. Cobertura da seleção

Para cada jogo:

```text
Cobertura = Σ p(resultado selecionado)
```

Exemplos:

```text
Seco 1: cobertura = p(1)
Duplo 1X: cobertura = p(1) + p(X)
Triplo 1X2: cobertura = 1
```

### 5. Ganho marginal da cobertura

Uma evolução planejada é avaliar diretamente:

```text
ΔP(13+) = P(13+ | cobertura adicionada)
         - P(13+ | configuração anterior)
```

A pergunta deixa de ser apenas:

> Qual resultado tem maior probabilidade?

E passa a incluir:

> Em qual jogo uma marcação adicional compra mais probabilidade de 13+ ou 14 pontos?

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

Isso permite comparar bilhetes de forma determinística, sem ruído de simulação.

### Valor da cobertura

Uma métrica planejada é:

```text
VC(j) = ΔP(13+) / marcações adicionais
```

Ela mede **quanto de probabilidade adicional de premiação cada marcação extra compra**.

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

> **P(13+) e P(14) são calculadas exatamente para avaliar o bilhete, mas o otimizador ainda não maximiza diretamente P(13+).**

Uma das principais evoluções planejadas é aproximar ou substituir a função objetivo atual por uma otimização orientada diretamente a `P(13+)`, mantendo desempenho computacional aceitável.

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
│   ├── constraints.py
│   ├── metrics.py
│   ├── preprocess_data.py
│   ├── train_model.py
│   ├── predict_results.py
│   └── optimize_ticket.py
│
└── main.py
```

### Arquitetura planejada

```text
scripts/
├── common.py
├── preprocess_data.py
├── train_model.py
├── predict_results.py
├── optimize_ticket.py
├── metrics.py
├── constraints.py
├── telemetry.py
├── backtest.py
└── calibration.py
```

A separação desejada é:

- **modelo** → estima probabilidades;
- **otimizador** → monta o bilhete;
- **métricas** → calcula P(14), P(13+), P(12+), Brier, Log Loss etc.;
- **constraints** → centraliza hard e soft constraints;
- **telemetria** → explica decisões;
- **backtest** → mede desempenho histórico sem vazamento temporal.

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

## Telemetria atual

Para cada partida, o terminal exibe:

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

---

## Próxima evolução: análise marginal

A telemetria deve evoluir para mostrar não apenas **qual solução venceu**, mas também **quanto custariam as alternativas**.

Exemplo desejado:

```text
=========== ANÁLISE MARGINAL ===========

JOGO 06 — REMO x SANTOS
Atual: 1X
P(13+) atual = 1.163062%

Alternativa 12:
P(13+) = 1.171800%
Δ = +0.008738 p.p.

Motivo de não selecionar:
- violaria a distribuição 10/6/5
```

Para o triplo:

```text
TRIPLO ATUAL: J13
P(13+) = 1.163062%

Triplo em J03: 1.151...
Triplo em J06: 1.158...
Triplo em J10: 1.155...
```

---

## Custo de oportunidade dos soft constraints

As preferências devem se tornar auditáveis em termos de perda real de probabilidade.

Exemplo:

```text
Melhor solução sem preferência:
P(13+) = 1.1820%

Melhor solução evitando vitória do Palmeiras:
P(13+) = 1.1630%

Custo absoluto = -0.0190 p.p.
Custo relativo = -1.61%
```

Fórmula:

```text
custo_relativo =
(P13_otimo - P13_alternativo) / P13_otimo
```

Isso permitirá substituir penalizações arbitrárias por regras como:

```text
Aplicar preferência apenas se custo relativo <= 2%
```

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
- custo dos soft constraints.

---

## Calibração das probabilidades

Antes de otimizar o bilhete, é importante verificar se as probabilidades são calibradas.

Exemplo:

> resultados estimados em torno de 60% deveriam ocorrer aproximadamente 60% das vezes.

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

O objetivo é evitar otimizar agressivamente probabilidades que estejam sistematicamente superestimadas ou subestimadas.

---

## Robustez

Uma solução não deve ser considerada forte apenas porque é ótima para um conjunto pontual de probabilidades.

Uma evolução planejada é perturbar as probabilidades dentro de faixas plausíveis e verificar:

- estabilidade do bilhete;
- estabilidade de P(13+);
- frequência com que cada seco, duplo ou triplo permanece selecionado.

Isso ajuda a identificar soluções excessivamente sensíveis a diferenças mínimas entre probabilidades próximas.

---

## Múltiplas soluções quase ótimas

Além do melhor bilhete, o sistema poderá retornar um conjunto de soluções próximas do ótimo:

```text
#1 P(13+) = 1.1631%
#2 P(13+) = 1.1618%
#3 P(13+) = 1.1609%
```

Isso permite escolher entre alternativas estatisticamente semelhantes usando os soft constraints sem pagar um custo probabilístico relevante.

---

## Validador independente

Além da validação executada ao final da otimização, o módulo `constraints.py` confere de forma independente:

```text
14 jogos
21 marcações
8 secos
5 duplos
1 triplo
10 top1
6 top2
5 top3
vitória do Flamengo incluída quando aplicável
```

Essa separação reduz o risco de um mesmo bug afetar geração e validação.

---

## Testes automatizados

Casos prioritários:

- desempate `1 > 2 > X`;
- probabilidades exatamente iguais;
- contagem `8/5/1`;
- contagem `10/6/5`;
- Flamengo como mandante;
- Flamengo como visitante;
- Palmeiras como mandante;
- Palmeiras como visitante;
- leitura decimal com vírgula;
- inexistência de solução válida;
- cálculo de `P(14)`;
- cálculo de `P(13+)`;
- consistência entre bilhete e auditoria final.

---

## Configuração externa

Uma evolução útil é retirar pesos e metas do código e centralizá-los em um arquivo como `config.yaml`:

```yaml
hard:
  secos: 8
  duplos: 5
  triplos: 1
  top1: 10
  top2: 6
  top3: 5

soft:
  mandante: 9
  empate: 6
  visitante: 6
  evitar_palmeiras: true
  max_custo_relativo_palmeiras: 0.02
```

Isso facilita backtests e comparação de estratégias sem alterar o código-fonte.

---

## Roadmap

### Implementado

- [x] leitura de `proximo_concurso.csv`;
- [x] ranking `top1/top2/top3`;
- [x] desempate `1 > 2 > X`;
- [x] entropia;
- [x] `gap12` e `gap23`;
- [x] otimização global por programação dinâmica;
- [x] hard constraint `8S / 5D / 1T`;
- [x] hard constraint `10 / 6 / 5`;
- [x] vitória do Flamengo obrigatória;
- [x] preferência contra vitória do Palmeiras;
- [x] preferência `9 / 6 / 6`;
- [x] auditoria final;
- [x] cálculo exato de `P(14)`;
- [x] cálculo exato de `P(13+)`;
- [x] cálculo e exibição de `P(12+)`;
- [x] validador independente das hard constraints;
- [x] exportação para `output/ticket.csv`.

### Próximas prioridades

- [ ] análise marginal de secos, duplos e triplo;
- [ ] custo absoluto e relativo dos soft constraints;
- [ ] otimização mais diretamente orientada a `P(13+)`;
- [ ] backtest walk-forward;
- [ ] calibração das probabilidades;
- [ ] testes automatizados.

### Evoluções posteriores

- [ ] robustez por perturbação de probabilidades;
- [ ] múltiplas soluções quase ótimas;
- [ ] configuração externa em YAML;
- [ ] comparação de diferentes funções objetivo;
- [ ] análise de valor marginal por marcação adicional;
- [ ] relatórios históricos consolidados.

---

## Filosofia do projeto

As probabilidades continuam sendo a base da estratégia, mas não devem determinar mecanicamente onde ficam secos, duplos e triplo.

O foco é responder duas perguntas diferentes:

1. **Qual resultado é mais provável em cada partida?**
2. **Em qual partida uma marcação adicional produz o maior ganho para o bilhete completo?**

A segunda pergunta é o núcleo da otimização.

> Não buscar apenas as 21 maiores probabilidades. Buscar a combinação de 21 marcações que produza o melhor bilhete possível sob as restrições definidas.

---

## Status

🚧 **Em desenvolvimento ativo.**

O projeto já gera um bilhete válido, audita as hard constraints, aplica as preferências estratégicas e calcula exatamente `P(14)` e `P(13+)` da solução gerada.

O próximo salto de qualidade é tornar as decisões cada vez mais **marginais, auditáveis e validadas fora da amostra**, reduzindo a dependência de pesos heurísticos e aproximando a otimização do objetivo final de premiação.
