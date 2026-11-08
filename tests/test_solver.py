import numpy as np
import pytest

from cprcheck.checks import reference_predict, run_checks
from cprcheck.data import IN_DIST, OOD, batch
from cprcheck.solver import HeatProblem, energy_balance, local_residual, solve


def manufactured(n):
    """k = 1, T = sin(pi x) sin(pi y) on the unit square, so q = 2 pi^2 sin(pi x) sin(pi y)."""
    c = (np.arange(n) + 0.5) / n
    X, Y = np.meshgrid(c, c)
    exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    return HeatProblem(q=2 * np.pi**2 * exact, k=np.ones((n, n)), L=1.0), exact


def test_second_order_convergence():
    errs = []
    for n in (16, 32, 64):
        p, exact = manufactured(n)
        errs.append(np.abs(solve(p) - exact).max())
    rates = [np.log2(errs[i] / errs[i + 1]) for i in range(2)]
    assert all(r > 1.8 for r in rates), (errs, rates)


@pytest.mark.parametrize("dist", [IN_DIST, *OOD.values()])
def test_reference_conserves_energy(dist):
    for p in batch(dist, 5, seed=3):
        T = solve(p)
        assert energy_balance(p, T) < 1e-12
        assert local_residual(p, T) < 1e-11
        assert T.min() > 0


def test_energy_balance_detects_a_wrong_field():
    p = batch(IN_DIST, 1, seed=4)[0]
    T = solve(p)
    assert energy_balance(p, 1.05 * T) == pytest.approx(0.05, rel=1e-9)
    assert local_residual(p, 1.05 * T) > 1e-3


def test_harmonic_mean_handles_material_interface():
    # Two slabs in series across x: the flux through the interface must be continuous,
    # which the discrete solution satisfies exactly with harmonic-mean face conductances.
    n = 20
    k = np.ones((n, n))
    k[:, n // 2 :] = 100.0
    q = np.zeros((n, n))
    q[n // 2 - 3 : n // 2 + 3, 2:4] = 1e3
    p = HeatProblem(q=q, k=k, L=1.0)
    T = solve(p)
    assert energy_balance(p, T) < 1e-12


def test_reference_passes_every_check():
    probs = batch(IN_DIST, 10, seed=5)
    r = run_checks(reference_predict, probs)
    assert r["accuracy"]["max_abs_err_K"] == 0.0
    assert r["conservation_5_3"]["energy_imbalance_max"] < 1e-12
    inv = r["invariants_5_3"]
    assert inv["superposition_violation_median"] < 1e-12
    assert inv["homogeneity_violation_median"] < 1e-12
    assert inv["mirror_violation_median"] < 1e-12
    assert inv["negative_rise_K_max"] == 0.0
    det = r["determinism_5_2"]
    assert det["repeat_bitwise_equal"] and det["batch1_vs_batchN_bitwise_equal"]


def test_checks_catch_a_nonlinear_surrogate():
    def squashed(problems):
        return [np.tanh(solve(p) / 10.0) * 10.0 for p in problems]

    r = run_checks(squashed, batch(IN_DIST, 10, seed=6))
    assert r["invariants_5_3"]["homogeneity_violation_median"] > 1e-3
    assert r["invariants_5_3"]["superposition_violation_median"] > 1e-3
    # tanh barely changes the cool edge cells, so the global balance looks almost fine;
    # the per-cell residual is what exposes it.
    assert r["conservation_5_3"]["local_residual_median"] > 1e-2


def test_checks_catch_batch_dependent_outputs():
    def batch_dependent(problems):
        return [solve(p) + 1e-6 * len(problems) for p in problems]

    det = run_checks(batch_dependent, batch(IN_DIST, 6, seed=7))["determinism_5_2"]
    assert det["repeat_bitwise_equal"]
    assert not det["batch1_vs_batchN_bitwise_equal"]
    assert det["batch1_vs_batchN_max_diff_K"] == pytest.approx(5e-6)
