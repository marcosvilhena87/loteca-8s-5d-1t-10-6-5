"""Métricas probabilísticas exatas para um bilhete Loteca."""

from __future__ import annotations

import math
from collections.abc import Iterable


def hit_distribution(coverages: Iterable[float]) -> tuple[float, ...]:
    """Calcula P(exatamente k acertos) por convolução de Bernoullis independentes."""
    distribution = [1.0]
    for coverage in coverages:
        if not math.isfinite(coverage) or not 0.0 <= coverage <= 1.0:
            raise ValueError(f"Cobertura inválida: {coverage!r}")
        distribution.append(0.0)
        for hits in range(len(distribution) - 1, 0, -1):
            distribution[hits] = (
                distribution[hits] * (1.0 - coverage)
                + distribution[hits - 1] * coverage
            )
        distribution[0] *= 1.0 - coverage
    return tuple(distribution)


def probability_at_least(coverages: Iterable[float], hits: int) -> float:
    """Retorna P(acertos >= hits), sem simulação Monte Carlo."""
    distribution = hit_distribution(coverages)
    if not 0 <= hits < len(distribution):
        raise ValueError(f"Número mínimo de acertos fora do intervalo: {hits}")
    return sum(distribution[hits:])
