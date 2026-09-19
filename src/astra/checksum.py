"""Family I: algebraic checksum invariants (Huang & Abraham, 1984).

For a product C = A @ B and a weight vector w, correct execution satisfies

    C @ w == A @ (B @ w)                                     (Eq. 1 in the paper)

With two weight vectors w1 = (1, 1, ..., 1) and w2 = (1, 2, ..., n), a single
corrupted entry in row i can be located and corrected:

    j = delta2 / delta1,   C[i, j] <- C[i, j] - delta1        (Eq. 2 in the paper)
"""

from __future__ import annotations

import numpy as np


def checksum_weights(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the two weight vectors used for localization."""
    return np.ones(n), np.arange(1, n + 1, dtype=float)


def encode_checksums(A: np.ndarray, B: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Return the reference checksum A @ (B @ w)."""
    return A @ (B @ w)


def locate_and_correct(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    tol: float = 0.0,
) -> tuple[np.ndarray, list[tuple[int, int, float]]]:
    """Detect, locate and correct single-entry corruptions in each row of C.

    Parameters
    ----------
    C : the (possibly corrupted) computed product.
    A, B : the input matrices.
    tol : discrepancies with absolute value <= tol are treated as round-off.

    Returns
    -------
    (C_corrected, corrections) where each correction is (row, column, magnitude).
    Rows whose discrepancy pattern is not consistent with a single corrupted
    entry are left untouched and reported by :func:`inconsistent_rows`.
    """
    n = C.shape[1]
    w1, w2 = checksum_weights(n)
    d1 = C @ w1 - encode_checksums(A, B, w1)
    d2 = C @ w2 - encode_checksums(A, B, w2)

    C_out = C.copy()
    corrections: list[tuple[int, int, float]] = []
    for i in range(C.shape[0]):
        if abs(d1[i]) <= tol:
            continue
        j_float = d2[i] / d1[i]
        j = int(round(j_float))
        if not (1 <= j <= n) or abs(j_float - j) > 1e-6:
            # Not consistent with exactly one corrupted entry in this row.
            continue
        C_out[i, j - 1] -= d1[i]
        corrections.append((i, j - 1, float(d1[i])))
    return C_out, corrections
