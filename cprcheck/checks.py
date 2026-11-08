"""Model-agnostic checks that turn criteria 5.2 and 5.3 into numbers.

A "model" is any callable `predict(problems) -> list[np.ndarray]` that maps a batch of
HeatProblem objects to temperature-rise fields. The reference solver satisfies every check
to round-off, which is what makes it a useful control.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from cprcheck.solver import HeatProblem, energy_balance, local_residual, solve

Predict = Callable[[Sequence[HeatProblem]], list[np.ndarray]]


def reference_predict(problems: Sequence[HeatProblem]) -> list[np.ndarray]:
    return [solve(p) for p in problems]


def _rel(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b) / np.linalg.norm(b))


def accuracy(predict: Predict, problems: Sequence[HeatProblem], truth: Sequence[np.ndarray]) -> dict:
    pred = predict(problems)
    rel = [_rel(p, t) for p, t in zip(pred, truth)]
    peak = [abs(p.max() - t.max()) for p, t in zip(pred, truth)]
    worst = [np.abs(p - t).max() for p, t in zip(pred, truth)]
    return {
        "rel_l2_median": float(np.median(rel)),
        "rel_l2_p95": float(np.percentile(rel, 95)),
        "peak_temp_err_K_median": float(np.median(peak)),
        "peak_temp_err_K_max": float(np.max(peak)),
        "max_abs_err_K": float(np.max(worst)),
    }


def conservation(predict: Predict, problems: Sequence[HeatProblem]) -> dict:
    """5.3: does the prediction conserve energy, globally and cell by cell?"""
    pred = predict(problems)
    eb = [energy_balance(p, T) for p, T in zip(problems, pred)]
    lr = [local_residual(p, T) for p, T in zip(problems, pred)]
    return {
        "energy_imbalance_median": float(np.median(eb)),
        "energy_imbalance_max": float(np.max(eb)),
        "local_residual_median": float(np.median(lr)),
    }


def invariants(predict: Predict, problems: Sequence[HeatProblem]) -> dict:
    """5.3: invariants every steady linear conduction solution satisfies.

    - superposition: for a fixed die, T(q1 + q2) = T(q1) + T(q2)
    - homogeneity:   T(2 q) = 2 T(q)
    - maximum principle: with q >= 0 and ambient edges, the rise is never negative
    - mirror symmetry: flipping the inputs flips the output
    """
    half = len(problems) // 2
    a, b = problems[:half], problems[half : 2 * half]
    summed = [HeatProblem(q=pa.q + pb.q, k=pa.k, L=pa.L) for pa, pb in zip(a, b)]
    b_on_a = [HeatProblem(q=pb.q, k=pa.k, L=pa.L) for pa, pb in zip(a, b)]
    doubled = [HeatProblem(q=2.0 * p.q, k=p.k, L=p.L) for p in problems]
    flipped = [HeatProblem(q=p.q[:, ::-1].copy(), k=p.k[:, ::-1].copy(), L=p.L) for p in problems]

    T = predict(problems)
    Ta = T[:half]
    Tb = predict(b_on_a)
    Tsum = predict(summed)
    T2 = predict(doubled)
    Tf = predict(flipped)
    sup = [_rel(s, x + y) for s, x, y in zip(Tsum, Ta, Tb)]
    hom = [_rel(d, 2.0 * x) for d, x in zip(T2, T)]
    flip = [_rel(f[:, ::-1], x) for f, x in zip(Tf, T)]
    neg = [float(-min(x.min(), 0.0)) for x in T]
    return {
        "superposition_violation_median": float(np.median(sup)),
        "homogeneity_violation_median": float(np.median(hom)),
        "mirror_violation_median": float(np.median(flip)),
        "negative_rise_K_max": float(np.max(neg)),
    }


def determinism(predict: Predict, problems: Sequence[HeatProblem], alternates: dict[str, Predict] | None = None) -> dict:
    """5.2: identical physical inputs must give identical outputs, intrinsically.

    Compares the same problems evaluated (a) twice, (b) one at a time versus as one batch,
    and (c) under any alternate execution settings the caller supplies (thread count, device).
    Reports whether results are bitwise identical and the largest difference in kelvin.
    """
    base = predict(problems)
    again = predict(problems)
    single = [predict([p])[0] for p in problems]
    out = {
        "repeat_bitwise_equal": all(np.array_equal(x, y) for x, y in zip(base, again)),
        "repeat_max_diff_K": float(max(np.abs(x - y).max() for x, y in zip(base, again))),
        "batch1_vs_batchN_bitwise_equal": all(np.array_equal(x, y) for x, y in zip(base, single)),
        "batch1_vs_batchN_max_diff_K": float(max(np.abs(x - y).max() for x, y in zip(base, single))),
    }
    for name, alt in (alternates or {}).items():
        other = alt(problems)
        out[f"{name}_bitwise_equal"] = all(np.array_equal(x, y) for x, y in zip(base, other))
        out[f"{name}_max_diff_K"] = float(max(np.abs(x - y).max() for x, y in zip(base, other)))
    return out


def run_checks(
    predict: Predict,
    problems: Sequence[HeatProblem],
    truth: Sequence[np.ndarray] | None = None,
    alternates: dict[str, Predict] | None = None,
) -> dict:
    truth = list(truth) if truth is not None else reference_predict(problems)
    return {
        "accuracy": accuracy(predict, problems, truth),
        "conservation_5_3": conservation(predict, problems),
        "invariants_5_3": invariants(predict, problems),
        "determinism_5_2": determinism(predict, problems, alternates),
    }
