# Evaluation protocol

This is the operational form of Section 7 of the paper. It is written so that a
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

## Rescoped single-node instantiation (Section 7.8)

When a large-scale platform or an architectural injector is unavailable, run
`experiments/run_campaign.py` instead. It differs from the full protocol in
four ways:

1. Bit flips are applied to array elements in memory, stratified by sign,
   exponent and mantissa, instead of being injected at the register level.
2. Workloads are dense matrix multiplication and conjugate gradient at sizes
   that fit one machine; the DNN workload is shrunk or dropped.
3. Baselines are unprotected execution and dual modular redundancy only.
4. Every metric of Table 3 is still measured, not estimated.

Consequences for the hypotheses:

| Hypothesis | Full protocol | Rescoped study |
| --- | --- | --- |
| H1 | coverage of architectural faults | coverage of corrupted data values |
| H2 | unchanged | unchanged |
| H3 | ASTRA vs. four baselines | ASTRA vs. unprotected and DMR |
| H4 | unchanged, at platform scale | unchanged, at single-node scale |

Report these narrowed claims explicitly; do not present rescoped coverage as
evidence about architectural faults.

Two further cautions that the harness makes visible:

- **Runtime is not the operation count.** The protected kernel uses an optimized
  BLAS routine while the verification is interpreted NumPy, so ASTRA can measure
  slower than DMR at small sizes. Proposition 1 is a statement about scalar
  multiplications; H3 is a statement about measured time. Keep them separate.
- **Rollback is not free accuracy.** Under a fixed iteration budget, restarting
  from a verified iterate can leave a larger final error than doing nothing,
  because the solver would have absorbed the corruption anyway. Report fidelity
  at equal budget and at equal wall-clock time.
- **Conjugate gradient heals itself.** With a generous iteration budget, many
  injected corruptions leave the final solution within tolerance and are
  therefore not significant errors at all. Report the number of significant
  faults alongside coverage, and state the iteration budget, otherwise coverage
  is uninterpretable.

## Reporting rules

- Report coverage against **significant** errors, at several output tolerances.
- Report medians and interquartile ranges for timings, not means alone.
- Report Holm-adjusted p-values for all pairwise overhead comparisons.
- State the measured forward-recovery rate p_c next to every waste figure.
- Publish the raw logs, not only the aggregates.
