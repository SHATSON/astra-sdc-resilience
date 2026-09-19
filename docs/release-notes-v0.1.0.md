# v0.1.0 — artifact accompanying the ASTRA paper

First public release. Contains the design and analytical artifact:

- Reference implementations of the four invariant families (`src/astra/`)
- Scripts that regenerate every figure in the paper (`figures/`)
- Fault-injection campaign templates for the three workload classes
  (`experiments/configs/`)
- Statistical analysis used by the protocol: Wilson score intervals, Wilcoxon
  signed-rank with Holm correction, and least-squares fit of measured waste to
  Eq. 9 (`analysis/analyze.py`)
- 36 unit tests, including the worked localization example of Figure 6 and the
  scaling corollary of Proposition 2
- Protocol, reproducibility checklist, and reference verification log (`docs/`)

**No experimental results.** The campaigns of Chapter 7 have not been run, so
`experiments/results/` contains only schemas and Tables 4 and 5 of the paper are
unpopulated.
