"""Family II: randomized verification certificates (Freivalds, 1977).

Verifies a claimed product C = A @ B with k matrix-vector products instead of a
full recomputation:

    A @ (B @ r) == C @ r                                     (Eq. 3 in the paper)

In exact arithmetic with r drawn uniformly from {0, 1}^n, an incorrect C passes
a single trial with probability at most 1/2, so k trials bound the probability
of a missed error by 2^-k. In floating-point arithmetic the equality is replaced
by the threshold test of Eq. 5.
"""

from __future__ import annotations

import numpy as np

EPS_DOUBLE = float(np.finfo(np.float64).eps)


def detection_threshold(
    A: np.ndarray,
    B: np.ndarray,
    r: np.ndarray,
    gamma: float = 10.0,
    eps: float = EPS_DOUBLE,
) -> float:
    """Precision-aware threshold tau of Eq. 5.

    tau = gamma * n * eps * ||A||_inf * ||B||_inf * ||r||_inf

    ``gamma`` is a safety factor that must be calibrated empirically on
    fault-free runs for the target platform and precision; the default is a
    starting point, not a validated value.
    """
    n = A.shape[1]
    inf = lambda M: float(np.linalg.norm(M, np.inf))
    return gamma * n * eps * inf(A) * inf(B) * float(np.max(np.abs(r)))


def freivalds_verify(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    k: int = 10,
    gamma: float = 10.0,
    rng: np.random.Generator | None = None,
) -> tuple[bool, float]:
    """Run k Freivalds trials.

    Returns ``(ok, max_discrepancy)``. ``ok`` is False as soon as a trial
    exceeds the threshold of Eq. 5.
    """
    rng = np.random.default_rng() if rng is None else rng
    n = A.shape[1]
    worst = 0.0
    for _ in range(k):
        r = rng.integers(0, 2, size=n).astype(float)
        d = A @ (B @ r) - C @ r
        gap = float(np.max(np.abs(d)))
        worst = max(worst, gap)
        if gap > detection_threshold(A, B, r, gamma=gamma):
            return False, worst
    return True, worst
