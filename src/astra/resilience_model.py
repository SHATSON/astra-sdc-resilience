"""Analytical resilience model (Chapter 6 of the paper).

Proposition 1: verification cost 3*k*n^2 against n^3 for classical
multiplication, so the ratio is 3k/n (Eq. 6).

Proposition 2: with forward-recovery probability p_c,

    W(T)  = (V + C) / T + lam * (1 - p_c) * T                (Eq. 9)
    T*    = sqrt((V + C) / (lam * (1 - p_c)))                (Eq. 10)
    W*    = 2 * sqrt(lam * (1 - p_c) * (V + C))              (Eq. 11)
"""

from __future__ import annotations

import math


def verification_ratio(n: int, k: int) -> float:
    """Eq. 6: scalar multiplications for verification divided by those for A @ B."""
    if n <= 0 or k <= 0:
        raise ValueError("n and k must be positive")
    return 3.0 * k / n


def waste(T: float, V: float, C: float, lam: float, p_c: float = 0.0) -> float:
    """Eq. 9: expected fraction of time wasted for period T."""
    _check(V, C, lam, p_c)
    if T <= 0:
        raise ValueError("T must be positive")
    return (V + C) / T + lam * (1.0 - p_c) * T


def optimal_period(V: float, C: float, lam: float, p_c: float = 0.0) -> float:
    """Eq. 10: period that minimizes Eq. 9."""
    _check(V, C, lam, p_c)
    return math.sqrt((V + C) / (lam * (1.0 - p_c)))


def minimum_waste(V: float, C: float, lam: float, p_c: float = 0.0) -> float:
    """Eq. 11: waste at the optimal period."""
    _check(V, C, lam, p_c)
    return 2.0 * math.sqrt(lam * (1.0 - p_c) * (V + C))


def _check(V: float, C: float, lam: float, p_c: float) -> None:
    if V < 0 or C < 0:
        raise ValueError("V and C must be non-negative")
    if lam <= 0:
        raise ValueError("lam must be positive")
    if not 0.0 <= p_c < 1.0:
        raise ValueError("p_c must satisfy 0 <= p_c < 1")
