"""Definição e validação independente das hard constraints do bilhete."""

from __future__ import annotations

from collections.abc import Sequence, Set

from .common import Match, OUTCOMES

TARGET_SIZES = (8, 5, 1)
TARGET_RANKS = (10, 6, 5)
TARGET_OUTCOMES = (9, 6, 6)
EXPECTED_MATCHES = 14
EXPECTED_MARKS = 21


def team_win(match: Match, team: str) -> str:
    """Retorna o resultado que representa a vitória de ``team`` na partida."""
    normalized = team.casefold()
    if match.home.casefold() == normalized:
        return "1"
    if match.away.casefold() == normalized:
        return "2"
    raise ValueError(f"{team} não participa do jogo {match.number}")


def is_team(match: Match, team: str) -> bool:
    normalized = team.casefold()
    return normalized in (match.home.casefold(), match.away.casefold())


def ticket_counts(
    matches: Sequence[Match], selections: Sequence[Set[str]]
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Calcula as contagens estruturais sem depender do otimizador."""
    sizes = tuple(sum(len(selection) == size for selection in selections) for size in (1, 2, 3))
    ranks = tuple(
        sum(match.ranking[index] in selection for match, selection in zip(matches, selections))
        for index in range(3)
    )
    outcomes = tuple(sum(result in selection for selection in selections) for result in OUTCOMES)
    return sizes, ranks, outcomes


def constraint_errors(matches: Sequence[Match], selections: Sequence[Set[str]]) -> list[str]:
    """Lista todas as violações, permitindo uma auditoria independente e completa."""
    errors: list[str] = []
    if len(matches) != EXPECTED_MATCHES:
        errors.append(f"quantidade de jogos {len(matches)} (esperado {EXPECTED_MATCHES})")
    if len(selections) != len(matches):
        errors.append(f"quantidade de palpites {len(selections)} (esperado {len(matches)})")

    for index, selection in enumerate(selections):
        if not selection or len(selection) > len(OUTCOMES) or not set(selection) <= set(OUTCOMES):
            number = matches[index].number if index < len(matches) else index + 1
            errors.append(f"palpite inválido no jogo {number}: {sorted(selection)}")

    if len(selections) == len(matches):
        sizes, ranks, _ = ticket_counts(matches, selections)
        if sizes != TARGET_SIZES:
            errors.append(f"estrutura {sizes} (esperado {TARGET_SIZES})")
        if ranks != TARGET_RANKS:
            errors.append(f"ranking {ranks} (esperado {TARGET_RANKS})")
        marks = sum(map(len, selections))
        if marks != EXPECTED_MARKS:
            errors.append(f"total de marcações {marks} (esperado {EXPECTED_MARKS})")
        for match, selection in zip(matches, selections):
            if is_team(match, "FLAMENGO/RJ") and team_win(match, "FLAMENGO/RJ") not in selection:
                errors.append(f"vitória do Flamengo ausente no jogo {match.number}")
    return errors


def validate_constraints(matches: Sequence[Match], selections: Sequence[Set[str]]) -> None:
    """Falha se o bilhete não cumprir integralmente as hard constraints."""
    errors = constraint_errors(matches, selections)
    if errors:
        raise ValueError("Bilhete inválido: " + "; ".join(errors))
