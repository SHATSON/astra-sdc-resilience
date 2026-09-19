"""ASTRA: Algorithmic STructure-aware Resilience Architecture (reference implementation).

This package contains small, readable reference implementations of the
invariant families described in the paper. It is written for clarity and for
reproducing the analytical figures, not for production performance.
"""

__version__ = "0.1.0"

from .checksum import (
    checksum_weights,
    encode_checksums,
    locate_and_correct,
)
from .freivalds import freivalds_verify, detection_threshold
from .iterative import residual_gap, conjugacy_gap
from .resilience_model import (
    verification_ratio,
    waste,
    optimal_period,
    minimum_waste,
)

__all__ = [
    "checksum_weights",
    "encode_checksums",
    "locate_and_correct",
    "freivalds_verify",
    "detection_threshold",
    "residual_gap",
    "conjugacy_gap",
    "verification_ratio",
    "waste",
    "optimal_period",
    "minimum_waste",
]
