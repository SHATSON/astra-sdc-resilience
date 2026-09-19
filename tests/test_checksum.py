import numpy as np
import pytest

from astra import locate_and_correct, freivalds_verify, checksum_weights


def paper_example():
    """The worked example shown as Figure 6 in the paper."""
    A = np.array([[1, 2, 0, 1], [0, 1, 3, 2], [2, 0, 1, 1], [1, 1, 1, 0]], dtype=float)
    B = np.array([[2, 1, 0, 1], [1, 0, 2, 1], [0, 3, 1, 2], [1, 1, 1, 1]], dtype=float)
    return A, B


def test_figure6_example_is_located_and_corrected():
    A, B = paper_example()
    C = A @ B
    corrupted = C.copy()
    corrupted[1, 2] += 5.0
    fixed, corrections = locate_and_correct(corrupted, A, B)
    assert corrections == [(1, 2, 5.0)]
    assert np.allclose(fixed, C)


def test_no_false_correction_on_clean_product():
    A, B = paper_example()
    C = A @ B
    fixed, corrections = locate_and_correct(C, A, B, tol=1e-9)
    assert corrections == []
    assert np.allclose(fixed, C)


@pytest.mark.parametrize("seed", range(20))
def test_random_single_entry_corruptions(seed):
    rng = np.random.default_rng(seed)
    n = 8
    A = rng.integers(-4, 5, size=(n, n)).astype(float)
    B = rng.integers(-4, 5, size=(n, n)).astype(float)
    C = A @ B
    i, j = rng.integers(0, n, size=2)
    magnitude = float(rng.choice([-7, -3, 2, 11]))
    corrupted = C.copy()
    corrupted[i, j] += magnitude
    fixed, corrections = locate_and_correct(corrupted, A, B, tol=1e-9)
    assert corrections == [(int(i), int(j), magnitude)]
    assert np.allclose(fixed, C)


def test_weights_have_expected_shape():
    w1, w2 = checksum_weights(5)
    assert np.allclose(w1, np.ones(5))
    assert np.allclose(w2, [1, 2, 3, 4, 5])


def test_burst_repairs_are_only_safe_when_reverified():
    """Two-vector localization assumes a single corrupted entry. Under a burst
    it can propose a plausible but wrong correction, so a repair must be
    accepted only after verification passes again."""
    from astra import inject_burst

    bad_repairs = 0
    for seed in range(40):
        rng = np.random.default_rng(seed)
        A, B = rng.standard_normal((32, 32)), rng.standard_normal((32, 32))
        golden = A @ B
        C = golden.copy()
        inject_burst(C, rng, 3)
        if np.allclose(C, golden):       # the flips were numerically negligible
            continue
        fixed, corrections = locate_and_correct(C, A, B, tol=1e-9)
        if not corrections:
            continue
        restored = np.allclose(fixed, golden)
        ok, _ = freivalds_verify(fixed, A, B, k=12, rng=np.random.default_rng(seed + 1))
        # Verification must never accept a product that was not restored.
        assert ok is False or restored
        bad_repairs += int(not restored)
    assert bad_repairs > 0, "expected at least one burst to defeat single-error localization"


def test_freivalds_accepts_correct_and_rejects_corrupted():
    rng = np.random.default_rng(0)
    n = 32
    A = rng.standard_normal((n, n))
    B = rng.standard_normal((n, n))
    C = A @ B
    ok, _ = freivalds_verify(C, A, B, k=10, rng=np.random.default_rng(1))
    assert ok
    corrupted = C.copy()
    corrupted[3, 7] += 1e-3
    ok, gap = freivalds_verify(corrupted, A, B, k=10, rng=np.random.default_rng(1))
    assert not ok
    assert gap > 0
