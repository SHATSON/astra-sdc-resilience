# v0.1.0 — artifact accompanying the ASTRA paper

First public release. Contains the design and analytical artifact:

- Reference implementations of the four invariant families (`src/astra/`)
- Scripts that regenerate every figure in the paper (`figures/`)
- Fault-injection campaign templates for the three workload classes
  (`experiments/configs/`)
- Statistical analysis used by the protocol: Wilson score intervals, Wilcoxon
  signed-rank with Holm correction, and least-squares fit of measured waste to
  Eq. 9 (`analysis/analyze.py`)
- A single-node campaign harness implementing the rescoped study of Section 7.8:
  software-level injection, matmul and CG workloads, ASTRA against unprotected
  execution and DMR, and every metric of Table 3 (`experiments/run_campaign.py`)
- 48 unit tests, including the worked localization example of Figure 6 and the
  scaling corollary of Proposition 2
- Protocol, reproducibility checklist, and reference verification log (`docs/`)

**Measurements included, with a narrow scope.** `experiments/results/` holds the
coverage, overhead and waste data of the single-node campaign, executed in a
shared single-vCPU container at n = 384 with software-level injection. The
full-scale campaign with an architectural injector has not been run, and the
checkpoint/restart and data-analytic baselines were not executed.
