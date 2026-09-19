"""Family III: convergence and recurrence invariants.

For the conjugate gradient method (Hestenes & Stiefel, 1952) the recursively
updated residual must agree with the true residual (Eq. 4 in the paper), and
search directions must remain mutually A-conjugate.
"""

from __future__ import annotations

import numpy as np


def residual_gap(A: np.ndarray, b: np.ndarray, x: np.ndarray, r: np.ndarray) -> float:
    """Relative gap between the recursive residual r and b - A @ x."""
    with np.errstate(over="ignore", invalid="ignore"):
        true_r = b - A @ x
        denom = float(np.linalg.norm(true_r)) or 1.0
        gap = float(np.linalg.norm(r - true_r) / denom)
    # A non-finite iterate or residual is unambiguously corrupt.
    if not (np.isfinite(gap) and np.all(np.isfinite(x)) and np.all(np.isfinite(r))):
        return float("inf")
    return gap


def conjugacy_gap(A: np.ndarray, p_old: np.ndarray, p_new: np.ndarray) -> float:
    """Scaled |p_old^T A p_new|, which is ~0 for uncorrupted CG directions."""
    num = abs(float(p_old @ (A @ p_new)))
    denom = float(np.linalg.norm(p_old) * np.linalg.norm(A @ p_new)) or 1.0
    return num / denom
