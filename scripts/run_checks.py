"""Run the 5.2 / 5.3 checks on the reference solver and the trained FNO, in and out of distribution."""

import json
import platform
from pathlib import Path

import numpy as np
import torch

from cprcheck.checks import reference_predict, run_checks
from cprcheck.data import IN_DIST, OOD, batch
from cprcheck.fno import FNO2d, make_predict
from cprcheck.solver import boundary_outflow, generated_power

ROOT = Path(__file__).resolve().parent.parent
N_EVAL = 100


def energy_rescaled(predict):
    """Post-hoc fix that forces the global energy balance to hold exactly."""

    def wrapped(problems):
        out = predict(problems)
        return [T * generated_power(p) / boundary_outflow(p, T) for p, T in zip(problems, out)]

    return wrapped


def with_threads(predict, n):
    def wrapped(problems):
        old = torch.get_num_threads()
        torch.set_num_threads(n)
        try:
            return predict(problems)
        finally:
            torch.set_num_threads(old)

    return wrapped


def main() -> None:
    model = FNO2d()
    model.load_state_dict(torch.load(ROOT / "results" / "fno.pt"))
    fno = make_predict(model)
    splits = {"in_distribution": IN_DIST, **OOD}
    results = {
        "env": {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__, "machine": platform.machine(), "threads_default": torch.get_num_threads(), "n_eval_per_split": N_EVAL},
        "splits": {},
    }
    for i, (name, dist) in enumerate(splits.items()):
        probs = batch(dist, N_EVAL, seed=1000 + i)
        truth = reference_predict(probs)
        results["splits"][name] = {
            "reference_solver": run_checks(reference_predict, probs, truth),
            "fno": run_checks(fno, probs, truth, alternates={"threads_1": with_threads(fno, 1)}),
            "fno_energy_rescaled": run_checks(energy_rescaled(fno), probs, truth),
        }
        print(name, "done", flush=True)
    (ROOT / "results" / "results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
