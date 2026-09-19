"""Smoke tests for the single-node harness of Section 7.8.

These check that the harness runs and emits the documented schemas. They do
not assert anything about coverage or overhead values: those are measurements,
and their values depend on the machine.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
import run_campaign as rc  # noqa: E402

TINY = {
    **rc.DEFAULTS,
    "workloads": [{"kernel": "matmul", "size": 32}, {"kernel": "cg", "size": 32}],
    "output_tolerance": [1e-8],
    "injection_trials": 5,
    "clean_verifications": 5,
    "timing_repetitions": 2,
    "freivalds_trials": 3,
    "cg_iterations": 40,
    "period_sweep_s": [0.05, 0.1],
    "waste_seconds_per_period": 0.2,
}


@pytest.fixture(autouse=True)
def _ignore_overflow_warnings():
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        yield


def test_coverage_rows_match_documented_schema():
    rows = rc.coverage_campaign(TINY, np.random.default_rng(0))
    assert rows
    expected = {"workload", "invariant_families", "output_tolerance",
                "significant_faults", "detected", "verifications_clean", "false_positives",
                "median_output_error_unprotected", "median_output_error_protected"}
    for row in rows:
        assert set(row) == expected
        assert row["detected"] <= row["significant_faults"]
        assert row["false_positives"] <= row["verifications_clean"]
        # Fidelity columns must be present and non-negative. They are NOT asserted
        # to favour ASTRA: under a fixed iteration budget, rolling a conjugate
        # gradient solver back to a verified iterate can end with a larger error
        # than letting the solver absorb the corruption itself. That is a finding
        # to report, not an invariant to enforce.
        for key in ("median_output_error_unprotected", "median_output_error_protected"):
            assert row[key] == "" or row[key] >= 0.0


def test_overhead_rows_are_paired_across_schemes():
    rows = rc.overhead_campaign(TINY, np.random.default_rng(0))
    assert {"astra", "dmr", "unprotected"} == {r["scheme"] for r in rows}
    for workload in {r["workload"] for r in rows}:
        counts = {}
        for r in rows:
            if r["workload"] == workload:
                counts[r["scheme"]] = counts.get(r["scheme"], 0) + 1
        assert len(set(counts.values())) == 1


def test_waste_rows_are_fractions():
    rows = rc.waste_campaign(TINY, np.random.default_rng(0))
    assert rows
    for row in rows:
        assert 0.0 <= row["waste"] <= 1.0
        assert row["period_s"] in TINY["period_sweep_s"]


def test_unprotected_matmul_keeps_the_corruption():
    rng = np.random.default_rng(0)
    A, B = rng.standard_normal((16, 16)), rng.standard_normal((16, 16))
    C, detected, repaired = rc.matmul_run(A, B, "unprotected", rng, True, 0, 10.0)
    assert not detected and not repaired
    assert not np.allclose(C, A @ B)


def test_astra_matmul_repairs_or_recomputes():
    rng = np.random.default_rng(1)
    A, B = rng.standard_normal((16, 16)), rng.standard_normal((16, 16))
    C, detected, _ = rc.matmul_run(A, B, "astra", rng, True, 8, 10.0)
    assert detected
    assert np.allclose(C, A @ B)
