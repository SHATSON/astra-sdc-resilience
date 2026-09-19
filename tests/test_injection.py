import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
from astra.injection import BIT_FIELDS, flip_bit, inject  # noqa: E402


def test_flip_bit_is_an_involution():
    for value in (1.0, -3.25, 1e-8, 6.02e23):
        for bit in (0, 17, 51, 52, 62, 63):
            assert flip_bit(flip_bit(value, bit), bit) == value


def test_sign_bit_flip_negates():
    assert flip_bit(2.5, 63) == -2.5
    assert flip_bit(-2.5, 63) == 2.5


def test_inject_modifies_the_array_in_place():
    rng = np.random.default_rng(3)
    a = np.ones((8, 8))
    event = inject(a, rng)
    assert a[event.index] == event.after
    assert event.after != event.before
    assert int(np.count_nonzero(a != 1.0)) == 1


@pytest.mark.parametrize("field", list(BIT_FIELDS))
def test_stratified_injection_uses_the_requested_field(field):
    rng = np.random.default_rng(7)
    a = np.full(64, 1.5)
    event = inject(a, rng, field=field)
    low, high = BIT_FIELDS[event.field]
    assert low <= event.bit <= high


def test_injected_values_stay_finite():
    rng = np.random.default_rng(11)
    a = np.full(256, 1.0)
    for _ in range(200):
        event = inject(a, rng)
        assert np.isfinite(event.after)
