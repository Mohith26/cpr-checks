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

| split | model | repeat bitwise | batch 1 vs N bitwise | batch max diff, K | 1 thread vs default bitwise | threads max diff, K |
|---|---|---|---|---|---|---|
| in_distribution | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| in_distribution | fno | True | False | 2.29e-05 | False | 5.72e-06 |
| in_distribution | fno_energy_rescaled | True | False | 2.90e-05 | n/a | n/a |
| more_hotspots | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| more_hotspots | fno | True | False | 3.81e-05 | False | 1.14e-05 |
| more_hotspots | fno_energy_rescaled | True | False | 3.08e-05 | n/a | n/a |
| higher_power | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| higher_power | fno | True | False | 6.10e-05 | False | 2.29e-05 |
| higher_power | fno_energy_rescaled | True | False | 2.46e-05 | n/a | n/a |
| high_k_contrast | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| high_k_contrast | fno | True | False | 2.67e-05 | False | 1.14e-05 |
| high_k_contrast | fno_energy_rescaled | True | False | 2.68e-05 | n/a | n/a |
| finer_grid_64 | reference_solver | True | True | 0.00e+00 | n/a | n/a |
| finer_grid_64 | fno | True | False | 1.72e-05 | False | 5.72e-06 |
| finer_grid_64 | fno_energy_rescaled | True | False | 1.83e-05 | n/a | n/a |
