"""Random chip-like conduction problems: hotspot power maps on a two-material die."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cprcheck.solver import HeatProblem


@dataclass(frozen=True)
class Distribution:
    """Knobs for the problem generator. The in-distribution defaults define the training set."""

    n: int = 32
    hotspots: tuple[int, int] = (1, 4)  # inclusive range of hotspot count
    power: tuple[float, float] = (2.5e8, 1.0e9)  # peak W/m^3 per hotspot
    k_base: float = 150.0  # silicon-like, W/(m K)
    k_low: tuple[float, float] = (15.0, 50.0)  # low-k inclusions, W/(m K)
    inclusions: tuple[int, int] = (0, 2)
    background: float = 0.05  # uniform leakage power as a fraction of peak


IN_DIST = Distribution()
OOD = {
    # each shift changes one thing relative to IN_DIST
    "more_hotspots": Distribution(hotspots=(6, 9)),
    "higher_power": Distribution(power=(2.0e9, 4.0e9)),
    "high_k_contrast": Distribution(k_low=(1.5, 5.0), inclusions=(2, 3)),
    "finer_grid_64": Distribution(n=64),
}


def _bump(n: int, cx: float, cy: float, w: float) -> np.ndarray:
    c = (np.arange(n) + 0.5) / n
    X, Y = np.meshgrid(c, c)
    return np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * w**2))


def sample(dist: Distribution, rng: np.random.Generator) -> HeatProblem:
    n = dist.n
    q = np.zeros((n, n))
    peak = 0.0
    for _ in range(rng.integers(dist.hotspots[0], dist.hotspots[1] + 1)):
        p = rng.uniform(*dist.power)
        peak = max(peak, p)
        q += p * _bump(n, rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85), rng.uniform(0.04, 0.12))
    q += dist.background * peak
    k = np.full((n, n), dist.k_base)
    c = (np.arange(n) + 0.5) / n
    X, Y = np.meshgrid(c, c)
    for _ in range(rng.integers(dist.inclusions[0], dist.inclusions[1] + 1)):
        x0, y0 = rng.uniform(0.1, 0.6, size=2)
        wx, wy = rng.uniform(0.15, 0.35, size=2)
        mask = (X >= x0) & (X < x0 + wx) & (Y >= y0) & (Y < y0 + wy)
        k[mask] = rng.uniform(*dist.k_low)
    return HeatProblem(q=q, k=k)


def batch(dist: Distribution, count: int, seed: int) -> list[HeatProblem]:
    rng = np.random.default_rng(seed)
    return [sample(dist, rng) for _ in range(count)]
