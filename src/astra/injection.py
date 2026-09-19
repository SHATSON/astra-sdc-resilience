"""Software-level fault injection for the rescoped single-node study.

The full protocol of the paper injects at the architectural level. This module
implements the weaker, single-node alternative described in Section 7.8: bit
flips applied to array elements in memory while a computation is in progress.
Coverage measured with this injector supports claims about corrupted data
values, not about architectural faults (see Section 8.3.1 of the paper).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# IEEE 754 double: bit 63 sign, bits 52-62 exponent, bits 0-51 mantissa.
BIT_FIELDS = {"sign": (63, 63), "exponent": (52, 62), "mantissa": (0, 51)}


@dataclass(frozen=True)
class Injection:
    """A single injected corruption."""

    index: tuple[int, ...]
    bit: int
    field: str
    before: float
    after: float

    @property
    def magnitude(self) -> float:
        return abs(self.after - self.before)


def flip_bit(value: float, bit: int) -> float:
    """Return ``value`` with the given bit of its IEEE 754 encoding flipped."""
    as_int = int(np.float64(value).view(np.int64))
    flipped = (as_int ^ (1 << bit)) & 0xFFFF_FFFF_FFFF_FFFF
    if flipped >= 1 << 63:  # wrap into the signed range that int64 accepts
        flipped -= 1 << 64
    return float(np.int64(flipped).view(np.float64))


def inject_burst(
    array: np.ndarray,
    rng: np.random.Generator,
    count: int = 3,
) -> list[Injection]:
    """Corrupt ``count`` entries of one row: the burst manifestation of the
    paper's fault model. A burst defeats single-error localization, so recovery
    falls back to recomputation or rollback."""
    row = int(rng.integers(0, array.shape[0])) if array.ndim > 1 else 0
    width = array.shape[-1]
    cols = rng.choice(width, size=min(count, width), replace=False)
    events = []
    for col in cols:
        view = array[row] if array.ndim > 1 else array
        low, high = BIT_FIELDS[str(rng.choice(list(BIT_FIELDS)))]
        bit = int(rng.integers(low, high + 1))
        before = float(view[col])
        after = flip_bit(before, bit)
        if not np.isfinite(after):
            lo_m, hi_m = BIT_FIELDS["mantissa"]
            bit = int(rng.integers(lo_m, hi_m + 1))
            after = flip_bit(before, bit)
        view[col] = after
        events.append(Injection((row, int(col)) if array.ndim > 1 else (int(col),),
                                bit, "burst", before, after))
    return events


def inject(
    array: np.ndarray,
    rng: np.random.Generator,
    field: str | None = None,
) -> Injection:
    """Flip one bit of one element of ``array`` in place.

    ``field`` selects the stratum (``"sign"``, ``"exponent"`` or
    ``"mantissa"``); ``None`` samples a field uniformly, which is the
    stratification the protocol requires.
    """
    if field is None:
        field = str(rng.choice(list(BIT_FIELDS)))
    low, high = BIT_FIELDS[field]
    bit = int(rng.integers(low, high + 1))
    flat = int(rng.integers(0, array.size))
    index = np.unravel_index(flat, array.shape)
    before = float(array[index])
    after = flip_bit(before, bit)
    if not np.isfinite(after):
        # A non-finite value is trivially detectable and is not informative
        # for coverage; resample once into the mantissa field instead.
        low_m, high_m = BIT_FIELDS["mantissa"]
        bit = int(rng.integers(low_m, high_m + 1))
        field = "mantissa"
        after = flip_bit(before, bit)
    array[index] = after
    return Injection(tuple(int(i) for i in index), bit, field, before, after)
