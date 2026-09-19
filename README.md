# ASTRA — Algorithmic STructure-aware Resilience Architecture

Reference implementation, figure sources, and evaluation protocol for the paper

> **Exploiting Algorithmic Structure for Efficient Detection and Recovery from
> Silent Data Corruptions in Large-Scale Computing Systems**

[![tests](https://github.com/SHATSON/astra-sdc-resilience/actions/workflows/tests.yml/badge.svg)](https://github.com/SHATSON/astra-sdc-resilience/actions/workflows/tests.yml)

> **Before you publish this repository:** replace every `SHATSON`
> placeholder (in this file, `CITATION.cff`, and the paper's artifact statement)
> with the real account or organization name, and add the archival DOI once you
> deposit a release on Zenodo.

## Status

This release contains the **artifact for the analytical and design parts of the
paper**: the invariant implementations, the scripts that generate every figure,
the campaign configurations, and the statistical analysis code.

It contains **no experimental results**. The fault-injection campaigns described
in Chapter 7 of the paper have not been run yet, so `experiments/results/` holds
only file schemas. Tables 4 and 5 of the paper are deliberately unpopulated.

## What is here

```
src/astra/            reference implementations of the four invariant families
  checksum.py         Family I  — checksum encoding, localization, correction (Eq. 1–2)
  freivalds.py        Family II — randomized verification and threshold (Eq. 3, 5)
  iterative.py        Family III— residual and A-conjugacy gaps (Eq. 4)
  resilience_model.py Chapter 6 — Eq. 6 and Propositions 1–2 (Eq. 9–11)
figures/              scripts that regenerate every figure in the paper
  make_plots.py       Figures 6, 8, 9 (computed example and analytical curves)
  diagrams/           Graphviz sources for Figures 1–5, 7, 10
experiments/          campaign configurations and result schemas
analysis/analyze.py   Wilson intervals, Wilcoxon + Holm, fit of measured waste to Eq. 9
tests/                unit tests, including the worked example of Figure 6
docs/                 protocol, reproducibility checklist, reference verification log
paper/                the manuscript
```

## Quick start

```bash
git clone https://github.com/SHATSON/astra-sdc-resilience.git
cd astra-sdc-resilience
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                        # 36 tests
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

## Running a campaign

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
