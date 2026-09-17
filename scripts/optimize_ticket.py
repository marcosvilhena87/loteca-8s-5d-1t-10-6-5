"""Otimiza globalmente um bilhete Loteca sujeito às hard constraints do projeto."""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from dataclasses import dataclass
from pathlib import Path

try:
    from .common import Match, OUTCOMES, read_matches
except ImportError:  # execução direta: python scripts/optimize_ticket.py
    from common import Match, OUTCOMES, read_matches

TARGET_SIZES = (8, 5, 1)
TARGET_RANKS = (10, 6, 5)
TARGET_OUTCOMES = (9, 6, 6)


@dataclass(frozen=True)
class Ticket:
    matches: tuple[Match, ...]
    selections: tuple[frozenset[str], ...]
    score: float

    @property
    def coverage(self) -> tuple[float, ...]:
        return tuple(sum(m.probabilities[x] for x in s) for m, s in zip(self.matches, self.selections))

    def probability_at_least(self, hits: int) -> float:
        distribution = [1.0] + [0.0] * len(self.matches)
        for probability in self.coverage:
            for count in range(len(self.matches), 0, -1):
                distribution[count] = distribution[count] * (1 - probability) + distribution[count - 1] * probability
            distribution[0] *= 1 - probability
        return sum(distribution[hits:])


def _is_team(match: Match, team: str) -> bool:
    return match.home.upper() == team or match.away.upper() == team


def _team_win(match: Match, team: str) -> str:
    return "1" if match.home.upper() == team else "2"


def optimize(matches: list[Match]) -> Ticket:
    """DP exata para o objetivo aditivo, mantendo todas as contagens relevantes."""
    # estado: secos, duplos, triplos, top1, top2, top3, n1, nx, n2
    states: dict[tuple[int, ...], tuple[float, tuple[frozenset[str], ...]]] = {
        (0,) * 9: (0.0, ())
    }
    options = tuple(frozenset(c) for size in (1, 2, 3) for c in itertools.combinations(OUTCOMES, size))

    for index, match in enumerate(matches):
        next_states = {}
        rank_index = {result: rank for rank, result in enumerate(match.ranking)}
        for selection in options:
            if _is_team(match, "FLAMENGO/RJ") and _team_win(match, "FLAMENGO/RJ") not in selection:
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
            if _is_team(match, "PALMEIRAS/SP") and _team_win(match, "PALMEIRAS/SP") in selection:
                local -= 0.18
            delta = tuple(size_delta + ranks + outcomes)
            for state, (score, choices) in states.items():
                candidate = tuple(a + b for a, b in zip(state, delta))
                if any(candidate[i] > TARGET_SIZES[i] for i in range(3)):
                    continue
                if any(candidate[i + 3] > TARGET_RANKS[i] for i in range(3)):
                    continue
                remaining = len(matches) - index - 1
                if any(candidate[i] + remaining < TARGET_SIZES[i] for i in range(3)):
                    continue
                value = score + local
                previous = next_states.get(candidate)
                if previous is None or value > previous[0]:
                    next_states[candidate] = (value, choices + (selection,))
        states = next_states

    finalists = []
    for state, (base_score, selections) in states.items():
        if state[:3] != TARGET_SIZES or state[3:6] != TARGET_RANKS:
            continue
        deviation = sum(abs(state[6 + i] - TARGET_OUTCOMES[i]) for i in range(3))
        finalists.append((base_score - 0.08 * deviation, selections))
    if not finalists:
        raise ValueError("Não existe bilhete que satisfaça todas as hard constraints")
    score, selections = max(finalists, key=lambda item: item[0])
    ticket = Ticket(tuple(matches), selections, score)
    validate(ticket)
    return ticket


def counts(ticket: Ticket) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    sizes = tuple(sum(len(s) == size for s in ticket.selections) for size in (1, 2, 3))
    ranks = tuple(sum(m.ranking[i] in s for m, s in zip(ticket.matches, ticket.selections)) for i in range(3))
    outcomes = tuple(sum(result in s for s in ticket.selections) for result in OUTCOMES)
    return sizes, ranks, outcomes


def validate(ticket: Ticket) -> None:
    sizes, ranks, _ = counts(ticket)
    errors = []
    if sizes != TARGET_SIZES: errors.append(f"estrutura {sizes}")
    if ranks != TARGET_RANKS: errors.append(f"ranking {ranks}")
    if sum(map(len, ticket.selections)) != 21: errors.append("total diferente de 21")
    for match, selection in zip(ticket.matches, ticket.selections):
        if _is_team(match, "FLAMENGO/RJ") and _team_win(match, "FLAMENGO/RJ") not in selection:
            errors.append(f"vitória do Flamengo ausente no jogo {match.number}")
    if errors:
        raise ValueError("Bilhete inválido: " + ", ".join(errors))


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
    palmeiras = all(not (_is_team(m, "PALMEIRAS/SP") and _team_win(m, "PALMEIRAS/SP") in s) for m, s in zip(ticket.matches, ticket.selections))
    lines.extend(("=========== AUDITORIA FINAL ===========", f"[OK] {sizes[0]} secos, {sizes[1]} duplos, {sizes[2]} triplo, 21 marcações",
                  f"[OK] top1={ranks[0]}, top2={ranks[1]}, top3={ranks[2]}", f"[{'OK' if outcomes == TARGET_OUTCOMES else 'INFO'}] 1/X/2={outcomes[0]}/{outcomes[1]}/{outcomes[2]} (alvo 9/6/6)",
                  "[OK] Vitória do Flamengo incluída quando aplicável", f"[{'OK' if palmeiras else 'INFO'}] Vitória do Palmeiras {'excluída' if palmeiras else 'incluída com penalização'}",
                  f"P(14)={ticket.probability_at_least(14):.6%} P(13+)={ticket.probability_at_least(13):.6%}", "Solução válida: SIM"))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um bilhete Loteca globalmente otimizado")
    parser.add_argument("input", nargs="?", default="data/proximo_concurso.csv")
    parser.add_argument("--output", default="output/ticket.csv")
    args = parser.parse_args()
    ticket = optimize(read_matches(args.input))
    write_ticket(ticket, args.output)
    print(report(ticket))


if __name__ == "__main__":
    main()
