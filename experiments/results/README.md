# Result file schemas

This directory holds raw measurement output. **It is empty on purpose**: no
campaign has been run yet, and the paper reports no experimental numbers.
When a campaign finishes, drop the CSV files here using the schemas below so
that `analysis/analyze.py` can read them unchanged.

## `coverage.csv` — Table 4 of the paper (H1, H2)

| column | meaning |
| --- | --- |
| `workload` | campaign name, e.g. `matmul_dense` |
| `invariant_families` | families active, e.g. `I+II` |
| `output_tolerance` | tolerance used to classify a fault as significant |
| `significant_faults` | injected faults that violated the tolerance |
| `detected` | how many of those were detected |
| `verifications_clean` | verifications executed in fault-free runs |
| `false_positives` | detections in those fault-free runs |

## `overhead.csv` — Table 5 of the paper (H3)

| column | meaning |
| --- | --- |
| `workload` | campaign name |
| `scheme` | `astra`, `unprotected`, `dmr`, `checkpoint_verify`, `data_analytic` |
| `repetition` | 1..30+, paired across schemes |
| `overhead` | (t_protected − t_unprotected) / t_unprotected |

## `waste.csv` — Proposition 2 check (H4)

| column | meaning |
| --- | --- |
| `workload` | campaign name |
| `period_s` | verification-and-checkpoint period T in seconds |
| `waste` | measured fraction of wall-clock time not spent on useful progress |
| `forward_recovery_rate` | measured p_c over the same run |

Record the injection log (site, bit position, time, detector outcome, recovery
action) alongside these files; `docs/reproducibility-checklist.md` lists
everything the artifact is expected to contain.
