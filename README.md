# ASTRA — Algorithmic STructure-aware Resilience Architecture

Reference implementation, figure sources, and evaluation protocol for the paper

> **Exploiting Algorithmic Structure for Efficient Detection and Recovery from
> Silent Data Corruptions in Large-Scale Computing Systems**

[![tests](https://github.com/<your-github-username>/astra-sdc-resilience/actions/workflows/tests.yml/badge.svg)](https://github.com/<your-github-username>/astra-sdc-resilience/actions/workflows/tests.yml)

> **Before you publish this repository:** replace every `<your-github-username>`
> placeholder (in this file, `CITATION.cff`, and the paper's artifact statement)
> with the real account or organization name, and add the archival DOI once you
> deposit a release on Zenodo.

## Status

This release contains the artifact for the paper **and the measurements of the
single-node campaign reported in Section 7.10**: invariant implementations,
figure scripts, campaign configurations, statistical analysis code, and the
`coverage.csv`, `overhead.csv`, `waste.csv` and `environment.json` produced by
the executed run.

Those measurements come from a **shared single-vCPU Linux container** (about
3 GB RAM, Python 3.12.3, NumPy 2.4.4 on OpenBLAS 0.3.31), which is why the
problem size is n = 384 and why timings carry more variance than a dedicated
machine would show. Headline numbers: 99.95% coverage for dense matrix
multiplication at a 1e-8 tolerance and 66.0% for conjugate gradient, no false
positive in 20,000 fault-free verifications per workload, 17.1% median overhead
for the solver against 106.9% for DMR, and 211.0% for the dense product against
106.2% for DMR.

The **full-scale campaign** of Sections 7.1–7.7 (architectural injector, large
platform, DNN workload) has **not** been run. Do not cite this release as
evidence about architectural faults.

## What is here

```
src/astra/            reference implementations of the four invariant families
  checksum.py         Family I  — checksum encoding, localization, correction (Eq. 1–2)
  freivalds.py        Family II — randomized verification and threshold (Eq. 3, 5)
  iterative.py        Family III— residual and A-conjugacy gaps (Eq. 4)
  resilience_model.py Section 6 — Eq. 6 and Propositions 1–2 (Eq. 9–11)
figures/              scripts that regenerate every figure in the paper
  make_plots.py       Figures 6, 8, 9 (computed example and analytical curves)
  diagrams/           Graphviz sources for Figures 1–5, 7, 10
experiments/          campaign configurations, the single-node harness, result schemas
  run_campaign.py     rescoped single-node study of Section 7.8, end to end
  configs/            full-protocol templates plus single_node.yaml and a smoke config
analysis/analyze.py   Wilson intervals, Wilcoxon + Holm, fit of measured waste to Eq. 9
tests/                unit tests, including the worked example of Figure 6
docs/                 protocol, reproducibility checklist, reference verification log
paper/                the manuscript
```

## Quick start

```bash
git clone https://github.com/<your-github-username>/astra-sdc-resilience.git
cd astra-sdc-resilience
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                        # 48 tests
python figures/make_plots.py  # writes figures/out/fig6.png, fig8.png, fig9.png
bash figures/diagrams/make_diagrams.sh   # needs Graphviz; writes fig1–5, 7, 10
```

## Reproducing the paper's claims

| Claim in the paper | How to check it here |
| --- | --- |
| Figure 6 localization example | `pytest tests/test_checksum.py::test_figure6_example_is_located_and_corrected` |
| Eq. 2 corrects single-entry corruptions | `tests/test_checksum.py::test_random_single_entry_corruptions` |
| Proposition 1 (Eq. 6) | `astra.verification_ratio`; `tests/test_resilience_model.py` |
| Proposition 2 and its corollary (Eq. 9–11) | `tests/test_resilience_model.py::test_corollary_scaling_in_sqrt_one_minus_pc` |
| Figures 8 and 9 | `python figures/make_plots.py` |
| Sample size for the protocol | `python analysis/analyze.py` |

Figures 8 and 9 are analytical curves. Figure 9 uses hypothetical parameters
(V + C = 120 s, λ = 1/21,600 s⁻¹) purely to illustrate the model.

## Running the single-node study (Section 7.8)

The rescoped instantiation runs on one workstation. It injects bit flips in
software, uses matrix multiplication and conjugate gradient at single-node
sizes, compares ASTRA against unprotected execution and dual modular
redundancy, and measures every metric of Table 3 of the paper.

```bash
python experiments/run_campaign.py \
  --config experiments/configs/single_node_smoke.yaml --outdir /tmp/smoke   # minutes
python experiments/run_campaign.py \
  --config experiments/configs/single_node.yaml --outdir experiments/results # hours
python analysis/analyze.py --coverage experiments/results/coverage.csv \
                           --overhead experiments/results/overhead.csv \
                           --waste    experiments/results/waste.csv
```

The harness writes `environment.json` alongside the CSVs. Calibrate `gamma` on
your own machine before reporting, and treat the smoke config as a sanity check
only: its sample sizes are far below what the confidence intervals require.

**What this study can and cannot claim.** Software-level injection perturbs
values in memory, not the arithmetic units that produce them. Coverage measured
here supports claims about corrupted data values; claims about architectural
faults need the full protocol with a register-level injector. The paper states
this limitation in Section 8.3.1.

**Recovery can cost accuracy under a fixed budget.** Conjugate gradient absorbs
many corruptions on its own. When ASTRA rolls back to the last verified iterate
within a fixed iteration budget, it discards progress, so the protected run can
finish with a *larger* final error than an unprotected run that healed itself.
Measure fidelity at equal iteration budget and at equal wall-clock time, and
report both; do not assume protection improves the answer.

**Overhead is implementation-bound, not just asymptotic.** Proposition 1 counts
scalar multiplications. In this harness the protected kernel calls an optimized
BLAS `gemm` while the verification runs in interpreted NumPy code, so at small
matrix sizes ASTRA can measure *slower* than dual modular redundancy even
though it performs far fewer operations. Report the measured runtime, state the
sizes, and do not present the operation-count result as if it were a runtime
result.

**Baselines implemented here.** v0.1.0 implements unprotected execution and dual
modular redundancy (two replicas of the same code path, compared). The
checkpoint/restart and data-analytic baselines named in Section 7.5 of the paper
are part of the full protocol and are **not** implemented in this release; do not
report numbers for them from this harness.

## Running the full-scale campaign

1. Copy a template from `experiments/configs/` and fill in the `null` fields.
2. Calibrate the safety factor γ of Eq. 5 on fault-free runs.
3. Size the campaign with `python analysis/analyze.py` (sample-size line).
4. Run the injector, writing CSVs that match `experiments/results/README.md`.
5. Analyze: `python analysis/analyze.py --coverage ... --overhead ... --waste ...`
6. Record the environment listed in `docs/reproducibility-checklist.md`.

## Citing

See `CITATION.cff`. Please cite the paper, and the archival DOI of the release
you used once one exists.

## License

Code is released under the MIT License (`LICENSE`). The manuscript and other
documents in `paper/` and `docs/` are released under CC BY 4.0.
