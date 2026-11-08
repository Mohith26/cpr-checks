"""Render results/results.json as the markdown tables used in the README."""

import json
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "results" / "results.json").read_text())


def pct(x):
    return f"{100 * x:.2f}%" if x >= 1e-4 else f"{x:.1e}"


def main():
    rows = ["| split | model | rel L2 (median) | peak T err, K (max) | energy imbalance (median / max) | per-cell residual (median) | superposition | homogeneity | mirror | min rise, K |", "|---|---|---|---|---|---|---|---|---|---|"]
    for split, models in R["splits"].items():
        for name, r in models.items():
            a, c, i = r["accuracy"], r["conservation_5_3"], r["invariants_5_3"]
            rows.append(
                f"| {split} | {name} | {pct(a['rel_l2_median'])} | {a['peak_temp_err_K_max']:.3f} | {pct(c['energy_imbalance_median'])} / {pct(c['energy_imbalance_max'])} | {pct(c['local_residual_median'])} | {pct(i['superposition_violation_median'])} | {pct(i['homogeneity_violation_median'])} | {pct(i['mirror_violation_median'])} | {-i['negative_rise_K_max']:.3f} |"
            )
    det = ["| split | model | repeat bitwise | batch 1 vs N bitwise | batch max diff, K | 1 thread vs default bitwise | threads max diff, K |", "|---|---|---|---|---|---|---|"]
    for split, models in R["splits"].items():
        for name, r in models.items():
            d = r["determinism_5_2"]
            det.append(
                f"| {split} | {name} | {d['repeat_bitwise_equal']} | {d['batch1_vs_batchN_bitwise_equal']} | {d['batch1_vs_batchN_max_diff_K']:.2e} | {d.get('threads_1_bitwise_equal', 'n/a')} | {d['threads_1_max_diff_K']:.2e} |" if "threads_1_max_diff_K" in d else
                f"| {split} | {name} | {d['repeat_bitwise_equal']} | {d['batch1_vs_batchN_bitwise_equal']} | {d['batch1_vs_batchN_max_diff_K']:.2e} | n/a | n/a |"
            )
    print("\n".join(rows))
    print()
    print("\n".join(det))


if __name__ == "__main__":
    main()
