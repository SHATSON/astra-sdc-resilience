import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
from analyze import fit_waste, holm, wilson_interval, wilcoxon_signed_rank  # noqa: E402


def test_wilson_interval_is_inside_unit_range_and_contains_estimate():
    p, lo, hi = wilson_interval(99, 100)
    assert 0.0 <= lo <= p <= hi <= 1.0


def test_wilson_matches_published_value():
    # Textbook check: 50/100 gives roughly [0.404, 0.596].
    _, lo, hi = wilson_interval(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3)
    assert hi == pytest.approx(0.5962, abs=1e-3)


def test_holm_is_monotone_and_at_least_raw():
    raw = {"a": 0.01, "b": 0.04, "c": 0.03}
    adj = holm(raw)
    assert all(adj[k] >= raw[k] for k in raw)
    assert adj["a"] <= adj["c"] <= adj["b"]


def test_wilcoxon_detects_consistent_shift():
    a = [1.0 + 0.01 * i for i in range(30)]
    b = [2.0 + 0.01 * i for i in range(30)]
    _, p = wilcoxon_signed_rank(a, b)
    assert p < 0.001
    _, p_same = wilcoxon_signed_rank(a, a)
    assert p_same == 1.0


def test_fit_waste_recovers_known_parameters():
    vc, slope = 120.0, 1 / 21_600 * 0.25
    periods = [500, 1000, 2000, 3000, 5000, 8000]
    measured = [vc / t + slope * t for t in periods]
    fit = fit_waste(periods, measured)
    assert fit["V_plus_C"] == pytest.approx(vc, rel=1e-9)
    assert fit["lambda_times_one_minus_pc"] == pytest.approx(slope, rel=1e-9)
