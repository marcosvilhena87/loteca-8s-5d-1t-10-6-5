"""Utilitários compartilhados para leitura e validação dos concursos."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

OUTCOMES = ("1", "X", "2")
TIE_PRIORITY = {"1": 0, "2": 1, "X": 2}


@dataclass(frozen=True)
class Match:
    contest: int
    number: int
    home: str
    away: str
    day: str
    probabilities: dict[str, float]
    ranking: tuple[str, str, str]

    @property
    def entropy(self) -> float:
        from math import log

        return -sum(p * log(p) for p in self.probabilities.values() if p > 0)


def _decimal(value: str) -> float:
    return float(value.strip().replace(",", "."))


def rank_probabilities(probabilities: dict[str, float]) -> tuple[str, str, str]:
    """Ordena probabilidades aplicando o desempate obrigatório 1 > 2 > X."""
    return tuple(
        sorted(OUTCOMES, key=lambda result: (-probabilities[result], TIE_PRIORITY[result]))
    )  # type: ignore[return-value]


def read_matches(path: str | Path) -> list[Match]:
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source, delimiter=";"))
    matches = []
    for row in rows:
        probabilities = {
            "1": _decimal(row["p(1)"]),
            "X": _decimal(row["p(x)"]),
            "2": _decimal(row["p(2)"]),
        }
        total = sum(probabilities.values())
        if abs(total - 1.0) > 1e-5:
            raise ValueError(f"Jogo {row['Jogo']}: probabilidades somam {total:.6f}, não 1")
        matches.append(
            Match(
                int(row["Concurso"]), int(row["Jogo"]), row["Mandante"].strip(),
                row["Visitante"].strip(), row["Data"].strip(), probabilities,
                rank_probabilities(probabilities),
            )
        )
    if len(matches) != 14:
        raise ValueError(f"Um concurso deve possuir 14 jogos; foram encontrados {len(matches)}")
    if len({match.number for match in matches}) != 14:
        raise ValueError("Os números dos jogos devem ser únicos")
    return sorted(matches, key=lambda match: match.number)
