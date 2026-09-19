"""Statistical analysis for the evaluation protocol (Chapter 7 of the paper).

Implements exactly the procedures the paper commits to:
  * Wilson score intervals for coverage and false-positive proportions
  * required sample size for a target interval half-width
  * Wilcoxon signed-rank tests with Holm correction across baselines
  * least-squares fit of measured waste to Eq. 9

Usage
-----
    python analysis/analyze.py --coverage experiments/results/coverage.csv \
                               --overhead experiments/results/overhead.csv \
                               --waste    experiments/results/waste.csv

Any input that does not exist is skipped, so the script can be run as soon as
the first campaign finishes. Input schemas are documented in
experiments/results/README.md.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from typing import Iterable

Z975 = 1.959963984540054  # standard normal 97.5th percentile


def wilson_interval(successes: int, trials: int, z: float = Z975) -> tuple[float, float, float]:
    """Wilson (1927) score interval. Returns (point estimate, low, high)."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return p, max(0.0, centre - half), min(1.0, centre + half)


def trials_for_half_width(half_width: float, p_guess: float = 0.99, z: float = Z975) -> int:
    """Smallest n whose Wilson half-width is <= half_width at p_guess."""
    n = 10
    while True:
        _, lo, hi = wilson_interval(round(p_guess * n), n, z)
        if (hi - lo) / 2 <= half_width:
            return n
        n = int(n * 1.5) + 1


def wilcoxon_signed_rank(a: Iterable[float], b: Iterable[float]) -> tuple[float, float]:
    """Two-sided Wilcoxon signed-rank test; returns (statistic, p-value).

    Uses the normal approximation with continuity and tie correction, which is
    appropriate for the >= 30 repetitions the protocol requires.
    """
    diffs = [x - y for x, y in zip(a, b) if x != y]
    n = len(diffs)
    if n == 0:
        return 0.0, 1.0
    order = sorted(range(n), key=lambda i: abs(diffs[i]))
    ranks = [0.0] * n
    i = 0
    tie_term = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(diffs[order[j + 1]]) == abs(diffs[order[i]]):
            j += 1
        avg = (i + j) / 2 + 1
        t = j - i + 1
        tie_term += t ** 3 - t
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    w_plus = sum(r for r, d in zip(ranks, diffs) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, diffs) if d < 0)
    w = min(w_plus, w_minus)
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - tie_term / 48
    if var <= 0:
        return w, 1.0
    z = (abs(w - mean) - 0.5) / math.sqrt(var)
    p = 2 * (1 - _normal_cdf(z))
    return w, min(1.0, max(0.0, p))


def holm(p_values: dict[str, float]) -> dict[str, float]:
    """Holm (1979) step-down adjusted p-values."""
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running = 0.0
    for idx, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - idx) * p))
        adjusted[name] = running
    return adjusted


def fit_waste(periods: list[float], measured: list[float]) -> dict[str, float]:
    """Fit W(T) = (V+C)/T + s*T (Eq. 9) by linear least squares in 1/T and T.

    Returns the fitted V+C and s = lambda*(1-p_c), plus the implied optimum.
    """
    x1 = [1.0 / t for t in periods]
    x2 = list(periods)
    s11 = sum(a * a for a in x1)
    s22 = sum(b * b for b in x2)
    s12 = sum(a * b for a, b in zip(x1, x2))
    t1 = sum(a * y for a, y in zip(x1, measured))
    t2 = sum(b * y for b, y in zip(x2, measured))
    det = s11 * s22 - s12 * s12
    if det == 0:
        raise ValueError("degenerate design: vary the period more widely")
    vc = (t1 * s22 - t2 * s12) / det
    slope = (t2 * s11 - t1 * s12) / det
    out = {"V_plus_C": vc, "lambda_times_one_minus_pc": slope}
    if vc > 0 and slope > 0:
        out["T_star"] = math.sqrt(vc / slope)
        out["W_star"] = 2 * math.sqrt(vc * slope)
    return out


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coverage")
    ap.add_argument("--overhead")
    ap.add_argument("--waste")
    ap.add_argument("--half-width", type=float, default=0.005)
    args = ap.parse_args()

    print(f"Trials needed per configuration for +/-{args.half_width:.3%} "
          f"half-width at p = 0.99: {trials_for_half_width(args.half_width)}")

    if args.coverage and os.path.exists(args.coverage):
        print("\nDetection coverage (Wilson 95% intervals)")
        for row in _rows(args.coverage):
            p, lo, hi = wilson_interval(int(row["detected"]), int(row["significant_faults"]))
            print(f"  {row['workload']:<28} {p:6.2%}  [{lo:6.2%}, {hi:6.2%}]")

    if args.overhead and os.path.exists(args.overhead):
        print("\nPaired overhead comparisons (Wilcoxon signed-rank, Holm-adjusted)")
        rows = _rows(args.overhead)
        workloads = sorted({r["workload"] for r in rows})
        baselines = sorted({r["scheme"] for r in rows} - {"astra"})
        for workload in workloads:
            sel = [r for r in rows if r["workload"] == workload]
            astra = [float(r["overhead"]) for r in sel if r["scheme"] == "astra"]
            raw = {}
            for baseline in baselines:
                other = [float(r["overhead"]) for r in sel if r["scheme"] == baseline]
                if len(other) == len(astra) and astra:
                    _, p = wilcoxon_signed_rank(astra, other)
                    raw[baseline] = p
            for name, p in holm(raw).items():
                print(f"  {workload:<28} astra vs {name:<18} p_adj = {p:.4f}")

    if args.waste and os.path.exists(args.waste):
        print("\nFit of measured waste to Eq. 9")
        rows = _rows(args.waste)
        fit = fit_waste([float(r["period_s"]) for r in rows],
                        [float(r["waste"]) for r in rows])
        for key, value in fit.items():
            print(f"  {key:<28} {value:,.6g}")


if __name__ == "__main__":
    main()
