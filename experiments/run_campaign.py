"""Single-node fault-injection campaign (Section 7.8 of the paper).

Runs the rescoped instantiation of the protocol on one machine:

  * software-level bit flips instead of register-level injection,
  * dense matrix multiplication and conjugate gradient at single-node sizes,
  * ASTRA compared against unprotected execution and dual modular redundancy,
  * every metric of Table 3 measured rather than estimated.

Outputs `coverage.csv`, `overhead.csv` and `waste.csv` in the schemas that
`analysis/analyze.py` reads (see experiments/results/README.md).

Example
-------
    python experiments/run_campaign.py --config experiments/configs/single_node.yaml \
                                       --outdir experiments/results

Claims supported by this harness are narrower than those of the full protocol:
coverage is coverage of corrupted data values, not of architectural faults.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from astra import freivalds_verify, locate_and_correct, residual_gap  # noqa: E402
from astra.injection import inject, inject_burst  # noqa: E402

# --------------------------------------------------------------------------- #
# workloads
# --------------------------------------------------------------------------- #


def spd_matrix(n: int) -> np.ndarray:
    """1-D Laplacian: symmetric positive definite, well understood, cheap."""
    A = np.zeros((n, n))
    np.fill_diagonal(A, 2.0)
    idx = np.arange(n - 1)
    A[idx, idx + 1] = -1.0
    A[idx + 1, idx] = -1.0
    return A


def _blocked_matmul(A, B, block):
    """Deterministic blocked product. Every replica uses this one code path so
    that two fault-free executions agree bit for bit, which is what dual
    modular redundancy assumes."""
    n = A.shape[0]
    C = np.empty_like(A)
    for start in range(0, n, block):
        stop = min(start + block, n)
        C[start:stop] = A[start:stop] @ B
    return C


def matmul_run(A, B, scheme, rng, inject_fault, k, gamma):
    """Blocked product with optional protection. Returns (C, detected, repaired)."""
    block = max(1, A.shape[0] // 4)
    C = _blocked_matmul(A, B, block)
    detected = repaired = False
    if inject_fault:
        inject(C, rng)
    if scheme == "astra":
        ok, _ = freivalds_verify(C, A, B, k=k, gamma=gamma, rng=rng)
        if not ok:
            detected = True
            tol = 1e-6 * max(1.0, float(np.abs(C).max()))
            C_fixed, corrections = locate_and_correct(C, A, B, tol=tol)
            # Two-vector localization is only valid for a single corrupted entry.
            # A burst can produce a plausible but wrong correction, so the repair
            # is accepted only if verification passes afterwards.
            if corrections:
                ok_after, _ = freivalds_verify(C_fixed, A, B, k=k, gamma=gamma, rng=rng)
                if ok_after:
                    C, repaired = C_fixed, True
            if not repaired:                       # fall back to recomputation
                C = _blocked_matmul(A, B, block)
    elif scheme == "dmr":
        C2 = _blocked_matmul(A, B, block)          # second replica, same code path
        if not np.array_equal(C, C2):
            detected = True
            C = _blocked_matmul(A, B, block)       # re-execute; DMR cannot localize
    return C, detected, repaired


def _cg_step(A, state):
    """One conjugate gradient iteration on (x, r, p, rs)."""
    x, r, p, rs = state
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        Ap = A @ p
        denom = float(p @ Ap) or 1e-300
        alpha = rs / denom
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = float(r @ r)
        p_new = r + (rs_new / (rs or 1e-300)) * p
    return x, r, p_new, rs_new


def cg_run(A, b, scheme, rng, inject_fault, max_iter, check_every, tol):
    """Conjugate gradient with optional protection.

    ``astra``  Family III: the recursive residual is compared with the true
               residual every ``check_every`` iterations, and the solver
               restarts from the last verified iterate when they disagree.
    ``dmr``    two replicas of the same iteration run in lockstep and their
               iterates are compared; the fault strikes one replica only, and a
               mismatch rolls both back to the last agreed state. No oracle
               solution is used anywhere in this function.
    """
    state = (np.zeros(A.shape[0]), b.copy(), b.copy(), float(b @ b))
    replica = tuple(c.copy() if hasattr(c, "copy") else c for c in state) if scheme == "dmr" else None
    checkpoint = tuple(c.copy() if hasattr(c, "copy") else c for c in state)
    detected = repaired = False
    strike = int(rng.integers(1, max_iter)) if inject_fault else -1

    for it in range(1, max_iter + 1):
        state = _cg_step(A, state)
        if replica is not None:
            replica = _cg_step(A, replica)
        if it == strike:
            target = state[int(rng.integers(0, 3))]     # x, r or p, in place
            inject(target, rng)
        if state[3] < tol * tol:
            break

        due = it % check_every == 0 or it == max_iter
        if scheme == "astra" and due:
            if residual_gap(A, b, state[0], state[1]) > 1e-6:
                detected = repaired = True              # self-heal from verified iterate
                state = tuple(c.copy() if hasattr(c, "copy") else c for c in checkpoint)
            else:
                checkpoint = tuple(c.copy() if hasattr(c, "copy") else c for c in state)
        elif scheme == "dmr" and due:
            with np.errstate(over="ignore", invalid="ignore"):
                agree = np.array_equal(state[0], replica[0]) and np.array_equal(state[1], replica[1])
            if not agree:
                detected = True
                state = tuple(c.copy() if hasattr(c, "copy") else c for c in checkpoint)
            else:
                checkpoint = tuple(c.copy() if hasattr(c, "copy") else c for c in state)
            replica = tuple(c.copy() if hasattr(c, "copy") else c for c in state)
    return state[0], detected, repaired

# --------------------------------------------------------------------------- #
# campaigns
# --------------------------------------------------------------------------- #


def _rel_err(computed, golden, scale):
    """Relative max-norm error; a non-finite result counts as unusable (inf)."""
    with np.errstate(over="ignore", invalid="ignore"):
        if not np.all(np.isfinite(computed)):
            return float("inf")
        return float(np.abs(computed - golden).max()) / scale


def coverage_campaign(cfg, rng):
    """One injection per trial; the same corruption decides significance and detection."""
    rows = []
    tolerances = cfg["output_tolerance"]
    for workload in cfg["workloads"]:
        name, size = workload["kernel"], workload["size"]
        faults = {t: 0 for t in tolerances}
        hits = {t: 0 for t in tolerances}
        err_unprotected, err_protected = [], []      # output fidelity (Table 3)

        if name == "matmul":
            A, B = rng.standard_normal((size, size)), rng.standard_normal((size, size))
            golden = A @ B
            scale = float(np.abs(golden).max()) or 1.0
            for _ in range(cfg["injection_trials"]):
                C = _blocked_matmul(A, B, max(1, size // 4))
                inject(C, rng)
                err = _rel_err(C, golden, scale)
                err_unprotected.append(err)
                ok, _ = freivalds_verify(C, A, B, k=cfg["freivalds_trials"],
                                         gamma=cfg["gamma"], rng=rng)
                detected = not ok                # verify() returns True when clean
                C_protected = C
                if detected:                     # apply the recovery ASTRA would
                    C_protected, corrections = locate_and_correct(
                        C, A, B, tol=1e-6 * max(1.0, float(np.abs(C).max())))
                    if not corrections:
                        C_protected = _blocked_matmul(A, B, max(1, size // 4))
                err_protected.append(_rel_err(C_protected, golden, scale))
                for t in tolerances:
                    if err > t:
                        faults[t] += 1
                        hits[t] += int(detected)
            clean = fp = 0
            for _ in range(cfg["clean_verifications"]):
                ok, _ = freivalds_verify(A @ B, A, B, k=cfg["freivalds_trials"],
                                         gamma=cfg["gamma"], rng=rng)
                clean += 1
                fp += int(not ok)
        else:
            A = spd_matrix(size)
            b = rng.standard_normal(size)
            # reference is the fault-free run of the same solver and budget,
            # so that solver truncation error is not counted as corruption
            golden, _, _ = cg_run(A, b, "unprotected", np.random.default_rng(0), False,
                                  cfg["cg_iterations"], cfg["check_every"], cfg["cg_tolerance"])
            scale = float(np.abs(golden).max()) or 1.0
            for _ in range(cfg["injection_trials"]):
                seed = int(rng.integers(0, 2**32 - 1))
                x_raw, _, _ = cg_run(A, b, "unprotected", np.random.default_rng(seed), True,
                                     cfg["cg_iterations"], cfg["check_every"], cfg["cg_tolerance"])
                x_prot, detected, _ = cg_run(A, b, "astra", np.random.default_rng(seed), True,
                                             cfg["cg_iterations"], cfg["check_every"], cfg["cg_tolerance"])
                err = _rel_err(x_raw, golden, scale)
                err_unprotected.append(err)
                err_protected.append(_rel_err(x_prot, golden, scale))
                for t in tolerances:
                    if err > t:
                        faults[t] += 1
                        hits[t] += int(detected)
            clean = fp = 0
            for _ in range(cfg["clean_verifications"]):
                _, det, _ = cg_run(A, b, "astra", rng, False, cfg["cg_iterations"],
                                   cfg["check_every"], cfg["cg_tolerance"])
                clean += 1
                fp += int(det)

        for t in tolerances:
            rows.append({
                "workload": f"{name}_{size}",
                "invariant_families": "I+II" if name == "matmul" else "III",
                "output_tolerance": t,
                "significant_faults": faults[t],
                "detected": hits[t],
                "verifications_clean": clean,
                "false_positives": fp,
                "median_output_error_unprotected": float(np.median(err_unprotected)) if err_unprotected else "",
                "median_output_error_protected": float(np.median(err_protected)) if err_protected else "",
            })
    return rows


def overhead_campaign(cfg, rng):
    rows = []
    for workload in cfg["workloads"]:
        name, size = workload["kernel"], workload["size"]
        if name == "matmul":
            A, B = rng.standard_normal((size, size)), rng.standard_normal((size, size))
            call = lambda scheme: matmul_run(A, B, scheme, rng, False, cfg["freivalds_trials"], cfg["gamma"])
        else:
            A, b = spd_matrix(size), rng.standard_normal(size)
            call = lambda scheme: cg_run(A, b, scheme, rng, False, cfg["cg_iterations"],
                                         cfg["check_every"], cfg["cg_tolerance"])
        for rep in range(1, cfg["timing_repetitions"] + 1):
            base = _time(lambda: call("unprotected"))
            for scheme in ("astra", "dmr"):
                t = _time(lambda: call(scheme))
                rows.append({"workload": f"{name}_{size}", "scheme": scheme,
                             "repetition": rep, "overhead": (t - base) / base})
            rows.append({"workload": f"{name}_{size}", "scheme": "unprotected",
                         "repetition": rep, "overhead": 0.0})
    return rows


def waste_campaign(cfg, rng):
    """Measure waste over a sweep of periods at a fixed error rate (Eq. 9).

    One period is: work for ``period`` seconds (unprotected blocked products),
    then one verification and one checkpoint. Errors arrive as a Poisson
    process of rate ``error_rate_per_second``, so the probability that a period
    is struck is 1 - exp(-lambda * period). A detected-but-unrepaired error
    loses the whole period; verification and checkpoint time is always waste.
    """
    rows = []
    size = cfg["workloads"][0]["size"]
    block = max(1, size // 4)
    A, B = rng.standard_normal((size, size)), rng.standard_normal((size, size))
    lam = cfg["error_rate_per_second"]

    for period in cfg["period_sweep_s"]:
        useful = wasted = 0.0
        detections = repairs = periods = 0
        deadline = time.perf_counter() + cfg["waste_seconds_per_period"]
        while time.perf_counter() < deadline:
            # ---- work phase -------------------------------------------------
            work_start = time.perf_counter()
            C = None
            while time.perf_counter() - work_start < period:
                C = _blocked_matmul(A, B, block)
            work_time = time.perf_counter() - work_start

            # ---- did an error strike this period? ---------------------------
            struck = rng.random() < 1.0 - np.exp(-lam * period)
            if struck:
                if rng.random() < cfg.get("burst_fraction", 0.0):
                    inject_burst(C, rng, cfg.get("burst_size", 3))
                else:
                    inject(C, rng)

            # ---- verification -----------------------------------------------
            v_start = time.perf_counter()
            ok, _ = freivalds_verify(C, A, B, k=cfg["freivalds_trials"],
                                     gamma=cfg["gamma"], rng=rng)
            repaired = False
            if not ok:
                detections += 1
                tol = 1e-6 * max(1.0, float(np.abs(C).max()))
                C_fixed, corrections = locate_and_correct(C, A, B, tol=tol)
                if corrections:
                    ok_after, _ = freivalds_verify(C_fixed, A, B, k=cfg["freivalds_trials"],
                                                   gamma=cfg["gamma"], rng=rng)
                    repaired = bool(ok_after)
                repairs += int(repaired)
            v_time = time.perf_counter() - v_start

            # ---- checkpoint ---------------------------------------------------
            c_time = _time(lambda: np.array(C, copy=True))

            periods += 1
            if struck and not repaired:
                wasted += work_time          # rollback loses the period
            else:
                useful += work_time
            wasted += v_time + c_time
        total = useful + wasted
        rows.append({
            "workload": f"matmul_{size}",
            "period_s": period,
            "waste": wasted / total if total else 0.0,
            "forward_recovery_rate": repairs / detections if detections else "",
            "periods_executed": periods,
        })
    return rows


def _time(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


# --------------------------------------------------------------------------- #

DEFAULTS = {
    "seed": 20260919,
    "workloads": [{"kernel": "matmul", "size": 256}, {"kernel": "cg", "size": 256}],
    "output_tolerance": [1e-10, 1e-8, 1e-6],
    "injection_trials": 200,
    "clean_verifications": 200,
    "timing_repetitions": 30,
    "freivalds_trials": 10,
    "gamma": 10.0,
    "cg_iterations": 300,
    "check_every": 10,
    "cg_tolerance": 1e-10,
    "period_sweep_s": [0.5, 1, 2, 4, 8, 16],
    "waste_seconds_per_period": 5.0,
    "error_rate_per_second": 0.05,
    "burst_fraction": 0.5,      # share of strikes that are multi-entry bursts
    "burst_size": 3,
}


def load_config(path: str | None) -> dict:
    cfg = dict(DEFAULTS)
    if path:
        import yaml  # imported lazily so the harness runs without PyYAML
        with open(path) as fh:
            user = yaml.safe_load(fh) or {}
        cfg.update({k: v for k, v in user.items() if v is not None})
    return cfg


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config")
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "results"))
    ap.add_argument("--only", choices=["coverage", "overhead", "waste"], action="append")
    ap.add_argument("--workload", action="append",
                    help="restrict to these kernels (matmul, cg); repeatable. Useful for "
                         "splitting a campaign into chunks that fit a job-time limit.")
    ap.add_argument("--suffix", default="", help="appended to output file names when chunking")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.workload:
        cfg["workloads"] = [w for w in cfg["workloads"] if w["kernel"] in args.workload]
    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(cfg["seed"])
    wanted = args.only or ["coverage", "overhead", "waste"]

    sfx = args.suffix
    if "coverage" in wanted:
        write_csv(os.path.join(args.outdir, f"coverage{sfx}.csv"), coverage_campaign(cfg, rng))
    if "overhead" in wanted:
        write_csv(os.path.join(args.outdir, f"overhead{sfx}.csv"), overhead_campaign(cfg, rng))
    if "waste" in wanted:
        write_csv(os.path.join(args.outdir, f"waste{sfx}.csv"), waste_campaign(cfg, rng))

    env = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "config": cfg,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    env["chunk"] = {"only": wanted, "workloads": [w["kernel"] for w in cfg["workloads"]], "suffix": sfx}
    with open(os.path.join(args.outdir, f"environment{sfx}.json"), "w") as fh:
        json.dump(env, fh, indent=2)
    print(f"Wrote results and environment.json to {args.outdir}")
    print("Record the remaining items in docs/reproducibility-checklist.md before reporting.")


if __name__ == "__main__":
    main()
