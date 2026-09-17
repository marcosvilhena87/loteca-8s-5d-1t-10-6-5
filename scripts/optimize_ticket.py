"""Otimiza globalmente um bilhete Loteca sujeito às hard constraints do projeto."""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from dataclasses import dataclass
from pathlib import Path

from .common import Match, OUTCOMES, read_matches
from .constraints import (
    TARGET_OUTCOMES,
    TARGET_RANKS,
    TARGET_SIZES,
    is_team,
    team_win,
    ticket_counts,
    validate_constraints,
)
from .historical_patterns import historical_top1_runs, ticket_top1_runs
from .metrics import hit_distribution, probability_at_least


@dataclass(frozen=True)
class Ticket:
    matches: tuple[Match, ...]
    selections: tuple[frozenset[str], ...]
    score: float
    objective: str = "p13plus"
    objective_value: float = 0.0

    @property
    def coverage(self) -> tuple[float, ...]:
        # Arquivos decimais podem somar 1 ± 1e-9; cobertura continua sendo probabilidade.
        return tuple(min(1.0, max(0.0, sum(m.probabilities[x] for x in s)))
                     for m, s in zip(self.matches, self.selections))

    def probability_at_least(self, hits: int) -> float:
        return probability_at_least(self.coverage, hits)


OBJECTIVE_HITS = {"p14": 14, "p13plus": 13, "p12plus": 12}


def _exact_objective(coverages: tuple[float, ...], objective: str) -> float:
    """Calcula a métrica global usada para reranquear um bilhete completo."""
    distribution = hit_distribution(coverages)
    if objective in OBJECTIVE_HITS:
        return sum(distribution[OBJECTIVE_HITS[objective]:])
    if objective == "balanced":
        return 0.50 * sum(distribution[12:]) + 0.30 * sum(distribution[13:]) + 0.20 * distribution[14]
    raise ValueError(f"Objetivo desconhecido: {objective}")


def optimize_candidates(
    matches: list[Match], *, objective: str = "p13plus", top_n: int = 20,
) -> list[Ticket]:
    """Gera Top-N por estado e reranqueia finalistas pela probabilidade exata."""
    if objective not in (*OBJECTIVE_HITS, "balanced"):
        raise ValueError(f"Objetivo desconhecido: {objective}")
    if top_n < 1:
        raise ValueError("top_n deve ser maior ou igual a 1")
    # estado: secos, duplos, triplos, top1, top2, top3, n1, nx, n2
    states: dict[tuple[int, ...], list[tuple[float, tuple[frozenset[str], ...]]]] = {
        (0,) * 9: [(0.0, ())]
    }
    options = tuple(frozenset(c) for size in (1, 2, 3) for c in itertools.combinations(OUTCOMES, size))

    for index, match in enumerate(matches):
        next_states: dict[tuple[int, ...], list[tuple[float, tuple[frozenset[str], ...]]]] = {}
        rank_index = {result: rank for rank, result in enumerate(match.ranking)}
        for selection in options:
            if is_team(match, "FLAMENGO/RJ") and team_win(match, "FLAMENGO/RJ") not in selection:
                continue
            size_delta = [0, 0, 0]
            size_delta[len(selection) - 1] = 1
            ranks = [0, 0, 0]
            outcomes = [0, 0, 0]
            for result in selection:
                ranks[rank_index[result]] += 1
                outcomes[OUTCOMES.index(result)] += 1
            covered = sum(match.probabilities[result] for result in selection)
            # P(14) em log + cobertura marginal ponderada pela incerteza.
            local = math.log(covered) + 0.10 * match.entropy * (len(selection) - 1)
            if is_team(match, "PALMEIRAS/SP") and team_win(match, "PALMEIRAS/SP") in selection:
                local -= 0.18
            delta = tuple(size_delta + ranks + outcomes)
            for state, partials in states.items():
                candidate = tuple(a + b for a, b in zip(state, delta))
                if any(candidate[i] > TARGET_SIZES[i] for i in range(3)):
                    continue
                if any(candidate[i + 3] > TARGET_RANKS[i] for i in range(3)):
                    continue
                remaining = len(matches) - index - 1
                if any(candidate[i] + remaining < TARGET_SIZES[i] for i in range(3)):
                    continue
                bucket = next_states.setdefault(candidate, [])
                for score, choices in partials:
                    bucket.append((score + local, choices + (selection,)))
                bucket.sort(key=lambda item: item[0], reverse=True)
                del bucket[top_n:]
        states = next_states

    finalists: list[Ticket] = []
    for state, partials in states.items():
        if state[:3] != TARGET_SIZES or state[3:6] != TARGET_RANKS:
            continue
        for _, selections in partials:
            coverages = tuple(min(1.0, max(0.0, sum(match.probabilities[result] for result in selection)))
                              for match, selection in zip(matches, selections))
            exact_value = _exact_objective(coverages, objective)
            deviation = sum(abs(state[6 + i] - TARGET_OUTCOMES[i]) for i in range(3))
            includes_palmeiras = any(
                is_team(match, "PALMEIRAS/SP") and team_win(match, "PALMEIRAS/SP") in selection
                for match, selection in zip(matches, selections)
            )
            utility = math.log(max(exact_value, 1e-300)) - 0.01 * deviation
            utility -= 0.02 * includes_palmeiras
            finalists.append(Ticket(tuple(matches), selections, utility, objective, exact_value))
    if not finalists:
        raise ValueError("Não existe bilhete que satisfaça todas as hard constraints")
    finalists.sort(key=lambda ticket: ticket.score, reverse=True)
    for ticket in finalists:
        validate(ticket)
    return finalists


def optimize(matches: list[Match], *, objective: str = "p13plus", top_n: int = 20) -> Ticket:
    """Retorna o melhor bilhete após DP Top-N e reranqueamento exato."""
    return optimize_candidates(matches, objective=objective, top_n=top_n)[0]


def counts(ticket: Ticket) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    return ticket_counts(ticket.matches, ticket.selections)


def validate(ticket: Ticket) -> None:
    validate_constraints(ticket.matches, ticket.selections)


def write_ticket(ticket: Ticket, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter=";")
        writer.writerow(("Concurso", "Jogo", "Mandante", "Visitante", "Palpite", "Tipo", "Cobertura"))
        for match, selection, coverage in zip(ticket.matches, ticket.selections, ticket.coverage):
            ordered = "".join(result for result in OUTCOMES if result in selection)
            writer.writerow((match.contest, match.number, match.home, match.away, ordered,
                             ("SECO", "DUPLO", "TRIPLO")[len(selection) - 1], f"{coverage:.9f}"))


def report(ticket: Ticket) -> str:
    lines = []
    for match, selection, coverage in zip(ticket.matches, ticket.selections, ticket.coverage):
        p = match.probabilities
        lines.extend((f"JOGO {match.number:02d} — {match.home} x {match.away}",
                      f"Probabilidades: 1={p['1']:.4f} X={p['X']:.4f} 2={p['2']:.4f}",
                      f"Ranking: top1={match.ranking[0]} top2={match.ranking[1]} top3={match.ranking[2]}",
                      f"Entropia={match.entropy:.3f} gap12={p[match.ranking[0]]-p[match.ranking[1]]:.4f} gap23={p[match.ranking[1]]-p[match.ranking[2]]:.4f}",
                      f"Escolha={''.join(x for x in OUTCOMES if x in selection)} Tipo={( 'SECO','DUPLO','TRIPLO')[len(selection)-1]} Cobertura={coverage:.4f}", ""))
    sizes, ranks, outcomes = counts(ticket)
    palmeiras = all(not (is_team(m, "PALMEIRAS/SP") and team_win(m, "PALMEIRAS/SP") in s) for m, s in zip(ticket.matches, ticket.selections))
    numbers, sequence, run_data = ticket_top1_runs(ticket.matches, ticket.selections)
    history = historical_top1_runs(Path(__file__).parents[1] / "data/concursos_anteriores.csv")
    lines.extend(("=========== DISTRIBUIÇÃO TOP1 ===========",
                  "Jogos ordenados por p(top1): " + " ".join(f"{number:02d}" for number in numbers),
                  "Top1 presente:              " + "  ".join("1" if value else "0" for value in sequence),
                  "Runs: " + (" / ".join(map(str, run_data.runs)) or "nenhuma"),
                  f"Maior sequência: {run_data.max_run}",
                  f"Média das sequências: {run_data.mean_run:.2f}",
                  f"Número de sequências: {run_data.n_runs}",
                  f"Concentração: {run_data.concentration}",
                  f"Mediana histórica max_run: {history.median_max_run:.1f} ({history.contests} concursos)",
                  f"P histórico(max_run >= atual): {history.tail_probability(run_data.max_run):.2%}", "",
                  "=========== AUDITORIA FINAL ===========", f"[OK] {sizes[0]} secos, {sizes[1]} duplos, {sizes[2]} triplo, 21 marcações",
                  f"[OK] top1={ranks[0]}, top2={ranks[1]}, top3={ranks[2]}", f"[{'OK' if outcomes == TARGET_OUTCOMES else 'INFO'}] 1/X/2={outcomes[0]}/{outcomes[1]}/{outcomes[2]} (alvo 9/6/6)",
                  "[OK] Vitória do Flamengo incluída quando aplicável", f"[{'OK' if palmeiras else 'INFO'}] Vitória do Palmeiras {'excluída' if palmeiras else 'incluída com penalização'}",
                  f"Objetivo={ticket.objective} Valor={ticket.objective_value:.6%}",
                  f"P(14)={ticket.probability_at_least(14):.6%} P(13+)={ticket.probability_at_least(13):.6%} P(12+)={ticket.probability_at_least(12):.6%}",
                  probability_summary(ticket), "Solução válida: SIM"))
    return "\n".join(lines)


def probability_summary(ticket: Ticket) -> str:
    """Resume a distribuição exata de acertos além das faixas de premiação."""
    distribution = hit_distribution(ticket.coverage)
    expected = sum(hits * probability for hits, probability in enumerate(distribution))
    variance = sum((hits - expected) ** 2 * probability for hits, probability in enumerate(distribution))
    mode = max(range(len(distribution)), key=distribution.__getitem__)
    return (
        f"E[acertos]={expected:.3f} Desvio-padrão={math.sqrt(variance):.3f} "
        f"Moda={mode} P(11+)={sum(distribution[11:]):.6%} "
        f"P(10+)={sum(distribution[10:]):.6%}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um bilhete Loteca globalmente otimizado")
    parser.add_argument("input", nargs="?", default="data/proximo_concurso.csv")
    parser.add_argument("--output", default="output/ticket.csv")
    parser.add_argument("--objective", choices=(*OBJECTIVE_HITS, "balanced"), default="p13plus")
    parser.add_argument("--top-n", type=int, default=20, help="candidatos preservados por estado da DP")
    parser.add_argument("--alternatives", type=int, default=1, help="quantidade de finalistas exibidos")
    args = parser.parse_args()
    candidates = optimize_candidates(read_matches(args.input), objective=args.objective, top_n=args.top_n)
    ticket = candidates[0]
    write_ticket(ticket, args.output)
    print(report(ticket))
    if args.alternatives > 1:
        print("\n=========== ALTERNATIVAS QUASE ÓTIMAS ===========")
        for position, candidate in enumerate(candidates[:args.alternatives], 1):
            print(
                f"#{position} {candidate.objective}={candidate.objective_value:.6%} "
                f"P(14)={candidate.probability_at_least(14):.6%} "
                f"P(13+)={candidate.probability_at_least(13):.6%} "
                f"P(12+)={candidate.probability_at_least(12):.6%}"
            )


if __name__ == "__main__":
    main()
