# Evaluation protocol

This is the operational form of Chapter 7 of the paper. It is written so that a
reader can run the campaigns without inferring anything from prose.

## Hypotheses

| ID | Statement | Decided by |
| --- | --- | --- |
| H1 | Significant-error coverage is at least 99% for single-value corruptions | `coverage.csv` + Wilson interval |
| H2 | False-positive rate is below 1e-4 per verification on fault-free runs | `coverage.csv` clean columns |
| H3 | ASTRA overhead is below DMR overhead everywhere, and falls with problem size for dense kernels | `overhead.csv` + Wilcoxon/Holm |
| H4 | Measured optimum and waste agree with Proposition 2 | `waste.csv` + `fit_waste` |

A hypothesis that fails is reported as a finding. Nothing in this repository
assumes the hypotheses hold.

## Steps

1. **Environment freeze.** Record every item in `reproducibility-checklist.md`.
2. **Golden runs.** Execute each workload without faults. Store the reference
   output, the per-verification discrepancy distribution, and timings.
3. **Threshold calibration.** Choose γ (Eq. 5) as the smallest value for which
   the observed false-positive rate on the golden runs is below 1e-4. Record the
   calibration data; γ is platform- and precision-specific.
4. **Sample size.** `python analysis/analyze.py` prints the number of injection
   trials needed for a ±0.5 percentage-point Wilson half-width.
5. **Injection campaigns.** For each workload × protection scheme × fault
   manifestation, inject with stratification across sign, exponent and mantissa
   bits. Log site, bit, time, detector outcome, recovery action, and final
   output deviation.
6. **Timing runs.** At least 30 fault-free repetitions per configuration,
   paired across schemes so the Wilcoxon signed-rank test applies.
7. **Waste sweep.** Vary the period T over at least six values spanning the
   predicted optimum, at a fixed injected error rate.
8. **Analysis.** Run `analysis/analyze.py` over the three CSVs.

## Reporting rules

- Report coverage against **significant** errors, at several output tolerances.
- Report medians and interquartile ranges for timings, not means alone.
- Report Holm-adjusted p-values for all pairwise overhead comparisons.
- State the measured forward-recovery rate p_c next to every waste figure.
- Publish the raw logs, not only the aggregates.
