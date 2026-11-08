# cpr-checks

Executable checks for two of the six minimum criteria in Vinci Research's paper
[Continuous Physics Reasoning: Definition, Minimum Criteria, and the Role of Foundation Models for Physics](https://github.com/Vinci4d/continuous-physics-reasoning)
(Kabaria and Osentoski, April 2026):

- **5.2 Deterministic Physical Reasoning**: identical physical inputs give identical outputs, and the reproducibility is intrinsic.
- **5.3 Solver-Grade Correctness**: outputs are verifiable against a first-principles solver and respect physical invariants such as conservation of energy, including under extrapolation.

The paper states these criteria in words. This repo turns them into numbers you can compute for any
model that maps a physical problem to a field, and then runs them on a case study: a Fourier Neural
Operator (FNO) surrogate for steady 2D heat conduction on a chip-like die, compared against a
conservative finite-volume solver that serves as the control.

The paper is a classification framework and does not ship tests; nothing here is endorsed by or
affiliated with Vinci. Vinci's own model was not tested (it is not public).

## Headline findings (single training seed, 100 test problems per row)

1. **A 1.3% field error hid a 52% per-cell energy imbalance.** In distribution, the FNO's median
   relative L2 temperature error is 1.28%, which looks solver-grade. Plugging its prediction back into
   the discrete conservation law shows a median per-cell heat imbalance of 52% of the heat source, and
   the global energy balance is off by 3.2% (median) and 23.5% (worst case). Field accuracy alone does
   not certify 5.3.
2. **Global conservation checks can be gamed.** A one-line post-hoc rescale that forces the global
   energy balance to hold exactly (`fno_energy_rescaled`) passes the global check to round-off on every
   split while making the field error worse (1.28% to 3.26% in distribution, 12.5% to 68.7% under
   higher power) and leaving the per-cell imbalance unchanged. A 5.3 test should be local, not just global.
3. **Linearity breaks first under extrapolation.** Steady conduction is linear in the heat source, so
   doubling the power must double the temperature rise. The FNO violates this homogeneity by 2.1% in
   distribution, and on a split whose peak power is 2 to 4x the training maximum its error jumps to 12.5% with
   peak-temperature errors up to 78 K. With stronger conductivity contrast than training, the error is
   40.5% and peak errors reach 163 K.
4. **Resolution transfer looks fine on the field and fails on physics.** Evaluated zero-shot on a 64x64
   grid, the field error is still only 1.75%, but the global energy imbalance is 52% (median).
5. **Not bitwise reproducible across batch size or thread count.** Repeating the same call in the same
   process is bitwise identical, but evaluating a problem alone versus inside a batch of 100 changes the
   output by up to 6.1e-5 K, and 1 thread versus 6 threads changes it by up to 2.3e-5 K. The magnitudes
   are tiny, but under 5.2's "intrinsic" wording the result is a fail: the output depends on how the
   call was scheduled, not only on the physical input. The reference solver is bitwise identical in every case.
6. **Maximum principle.** With non-negative heat sources and ambient edges the temperature rise can never
   be negative. The FNO predicts negative rises of up to 0.39 K.

## Full results

Columns: median relative L2 error; worst peak-temperature error; global energy imbalance
`|boundary outflow - generated power| / generated power`; per-cell residual `||A T - q h^2|| / ||q h^2||`
using the solver's own discrete operator; median relative violation of superposition
`T(q1 + q2) = T(q1) + T(q2)`, homogeneity `T(2q) = 2T(q)` and mirror symmetry; smallest predicted rise.

| split | model | rel L2 (median) | peak T err, K (max) | energy imbalance (median / max) | per-cell residual (median) | superposition | homogeneity | mirror | min rise, K |
|---|---|---|---|---|---|---|---|---|---|
| in_distribution | reference_solver | 0.0e+00 | 0.000 | 1.1e-15 / 2.4e-15 | 2.0e-14 | 2.3e-16 | 0.0e+00 | 1.0e-15 | 0.000 |
| in_distribution | fno | 1.28% | 3.532 | 3.15% / 23.48% | 51.83% | 1.37% | 2.12% | 1.22% | -0.041 |
| in_distribution | fno_energy_rescaled | 3.26% | 8.547 | 0.0e+00 / 2.1e-16 | 52.69% | 7.73% | 11.65% | 2.69% | -0.041 |
| more_hotspots | reference_solver | 0.0e+00 | 0.000 | 1.3e-15 / 2.6e-15 | 2.4e-14 | 2.3e-16 | 0.0e+00 | 1.0e-15 | 0.000 |
| more_hotspots | fno | 2.15% | 10.834 | 9.25% / 79.37% | 82.53% | 7.57% | 9.14% | 1.75% | -0.188 |
| more_hotspots | fno_energy_rescaled | 9.91% | 22.821 | 0.0e+00 / 2.1e-16 | 75.89% | 50.68% | 58.68% | 4.40% | -0.153 |
| higher_power | reference_solver | 0.0e+00 | 0.000 | 1.2e-15 / 3.9e-15 | 2.0e-14 | 2.2e-16 | 0.0e+00 | 1.0e-15 | 0.000 |
| higher_power | fno | 12.48% | 78.498 | 216.35% / 617.16% | 465.66% | 10.49% | 12.74% | 4.04% | -0.018 |
| higher_power | fno_energy_rescaled | 68.74% | 163.511 | 0.0e+00 / 2.1e-16 | 158.72% | 47.96% | 51.28% | 6.07% | -0.008 |
| high_k_contrast | reference_solver | 0.0e+00 | 0.000 | 6.6e-16 / 3.9e-15 | 1.9e-14 | 2.3e-16 | 0.0e+00 | 8.6e-16 | 0.000 |
| high_k_contrast | fno | 40.50% | 163.106 | 57.69% / 274.58% | 492.51% | 8.40% | 12.62% | 8.34% | -0.390 |
| high_k_contrast | fno_energy_rescaled | 59.59% | 186.681 | 0.0e+00 / 2.1e-16 | 311.32% | 13.29% | 25.19% | 12.02% | -0.261 |
| finer_grid_64 | reference_solver | 0.0e+00 | 0.000 | 8.7e-15 / 1.8e-14 | 8.2e-14 | 2.6e-16 | 0.0e+00 | 2.8e-15 | 0.000 |
| finer_grid_64 | fno | 1.75% | 1.269 | 51.73% / 139.75% | 302.20% | 1.44% | 2.62% | 1.33% | -0.114 |
| finer_grid_64 | fno_energy_rescaled | 33.68% | 14.538 | 0.0e+00 / 2.2e-16 | 198.55% | 17.46% | 25.22% | 3.94% | -0.069 |

Determinism (5.2):

| split | model | repeat bitwise | batch 1 vs N bitwise | batch max diff, K | 1 thread vs default bitwise | threads max diff, K |
|---|---|---|---|---|---|---|
| in_distribution | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| in_distribution | fno | True | False | 2.29e-05 | False | 5.72e-06 |
| more_hotspots | fno | True | False | 3.81e-05 | False | 1.14e-05 |
| higher_power | fno | True | False | 6.10e-05 | False | 2.29e-05 |
| high_k_contrast | fno | True | False | 2.67e-05 | False | 1.14e-05 |
| finer_grid_64 | fno | True | False | 1.72e-05 | False | 5.72e-06 |

Every row, including the rescaled variant and all reference-solver rows, is in
[`results/tables.md`](results/tables.md); raw numbers are in [`results/results.json`](results/results.json).

## The setup

- **Physics.** Steady conduction `-div(k grad T) = q` on a 10 mm square die whose edges are held at
  ambient (an idealized peripheral heat sink). Heat sources are 1 to 4 Gaussian hotspots plus uniform
  leakage; the die is silicon-like (k = 150 W/m/K) with up to two rectangular low-k inclusions
  (15 to 50 W/m/K). Temperatures are reported as the rise above ambient. This is a 2D model problem,
  not a real package stack.
- **Reference solver** ([`cprcheck/solver.py`](cprcheck/solver.py)). Cell-centred finite volumes with
  harmonic-mean face conductivities, which is exactly conservative: its global energy balance holds to
  about 1e-15. Tests check second-order convergence on a manufactured solution and conservation across
  material interfaces.
- **Surrogate** ([`cprcheck/fno.py`](cprcheck/fno.py)). A 4-layer FNO (width 32, 12 modes) trained on
  1,000 in-distribution problems at 32x32 for 150 epochs with a relative-L2 loss, on CPU. Final training
  error 0.61%.
- **Out-of-distribution splits** ([`cprcheck/data.py`](cprcheck/data.py)). Each changes one thing:
  6 to 9 hotspots, peak power 2 to 4x the training maximum, low-k inclusions down to 1.5 W/m/K, or a 64x64 grid.
- **Checks** ([`cprcheck/checks.py`](cprcheck/checks.py)). Model-agnostic: anything with
  `predict(problems) -> list[np.ndarray]` can be checked, and the reference solver is the control that
  must pass everything.

## Run it

```bash
python -m venv .venv && .venv/bin/pip install numpy scipy torch pytest
.venv/bin/python -m pytest -q tests            # 11 tests, about a second on an idle machine
PYTHONPATH=. .venv/bin/python scripts/train_fno.py   # writes results/fno.pt
PYTHONPATH=. .venv/bin/python scripts/run_checks.py  # writes results/results.json
PYTHONPATH=. .venv/bin/python scripts/make_table.py
```

The trained weights used for the tables are committed as `results/fno.pt`.

## What was and was not run

- Run: everything above, on Apple Silicon (arm64) CPU, Python 3.12, PyTorch 2.15, one training seed,
  100 evaluation problems per split.
- Not run: GPU or MPS execution (so no cross-device determinism numbers), multiple training seeds,
  larger or better-regularized surrogates, physics-informed losses, or 3D stacks. A bigger FNO or a
  residual loss would likely shrink some of these numbers; the point of the repo is that the checks
  expose the gaps, not that FNOs are bad.
- Not tested: a linearity-aware wrapper (normalize the source, predict, rescale) would make the
  homogeneity check pass by construction. That would be a reasonable next experiment.

## Using the checks on another model

```python
from cprcheck.checks import run_checks
from cprcheck.data import IN_DIST, batch

problems = batch(IN_DIST, 100, seed=0)
report = run_checks(my_predict, problems, alternates={"gpu": my_predict_on_gpu})
```

`alternates` lets you compare any execution setting (device, precision, thread count) against the
default for the 5.2 bitwise check.

## License

MIT
