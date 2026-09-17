"""Estatísticas de dispersão das ocorrências de top1 no histórico."""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunStats:
    """Resumo das sequências consecutivas de valores verdadeiros."""

    runs: tuple[int, ...]
    max_run: int
    mean_run: float
    n_runs: int
    concentration: int


@dataclass(frozen=True)
class HistoricalRunSummary:
    contests: int
    median_max_run: float
    max_runs: tuple[int, ...]

    def tail_probability(self, value: int) -> float:
        """Fração empírica dos concursos cujo max_run é ao menos ``value``."""
        return sum(run >= value for run in self.max_runs) / self.contests


def run_stats(sequence: list[bool] | tuple[bool, ...]) -> RunStats:
    """Calcula runs, maior run, média e concentração (soma dos quadrados)."""
    runs: list[int] = []
    current = 0
    for selected in sequence:
        if selected:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    if current:
        runs.append(current)
    frozen = tuple(runs)
    return RunStats(
        frozen,
        max(frozen, default=0),
        statistics.fmean(frozen) if frozen else 0.0,
        len(frozen),
        sum(length * length for length in frozen),
    )


def historical_top1_runs(path: str | Path) -> HistoricalRunSummary:
    """Lê concursos completos e mede top1_hit após ordenar por p(top1)."""
    by_contest: dict[int, list[tuple[float, int, bool]]] = {}
    # A base legada é exportada em Windows-1252 (acentos em nomes/dias).
    with Path(path).open(encoding="cp1252", newline="") as source:
        for row in csv.DictReader(source, delimiter=";"):
            contest = int(row["Concurso"])
            probability = float(row["p(top1)"].replace(",", "."))
            hit = row["top1"].strip() == "1"
            by_contest.setdefault(contest, []).append((probability, int(row["Jogo"]), hit))

    incomplete = [contest for contest, rows in by_contest.items() if len(rows) != 14]
    if incomplete:
        raise ValueError(f"Concursos históricos incompletos: {incomplete[:5]}")
    max_runs = tuple(
        run_stats(tuple(hit for _, _, hit in sorted(rows, key=lambda item: (-item[0], item[1])))).max_run
        for _, rows in sorted(by_contest.items())
    )
    if not max_runs:
        raise ValueError("Histórico vazio")
    return HistoricalRunSummary(len(max_runs), statistics.median(max_runs), max_runs)


def ticket_top1_runs(matches, selections) -> tuple[tuple[int, ...], tuple[bool, ...], RunStats]:
    """Mede a presença de top1 no bilhete em ordem decrescente de confiança."""
    ordered = sorted(
        zip(matches, selections),
        key=lambda item: (-item[0].probabilities[item[0].ranking[0]], item[0].number),
    )
    numbers = tuple(match.number for match, _ in ordered)
    sequence = tuple(match.ranking[0] in selection for match, selection in ordered)
    return numbers, sequence, run_stats(sequence)
