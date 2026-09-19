import math

import pytest

from astra import verification_ratio, waste, optimal_period, minimum_waste


def test_verification_ratio_matches_equation_6():
    assert verification_ratio(n=10_000, k=10) == pytest.approx(3e-3)


def test_optimal_period_minimizes_waste():
    V, C, lam, p_c = 60.0, 60.0, 1 / 21_600, 0.5
    T_star = optimal_period(V, C, lam, p_c)
    w_star = waste(T_star, V, C, lam, p_c)
    assert w_star == pytest.approx(minimum_waste(V, C, lam, p_c))
    for delta in (0.5, 0.9, 1.1, 2.0):
        assert waste(T_star * delta, V, C, lam, p_c) >= w_star - 1e-12


def test_corollary_scaling_in_sqrt_one_minus_pc():
    V, C, lam = 60.0, 60.0, 1 / 21_600
    base_T, base_W = optimal_period(V, C, lam), minimum_waste(V, C, lam)
    for p_c in (0.25, 0.5, 0.75, 0.9):
        factor = math.sqrt(1.0 - p_c)
        assert minimum_waste(V, C, lam, p_c) == pytest.approx(base_W * factor)
        assert optimal_period(V, C, lam, p_c) == pytest.approx(base_T / factor)


@pytest.mark.parametrize("bad", [{"lam": 0.0}, {"p_c": 1.0}, {"p_c": -0.1}, {"V": -1.0}])
def test_invalid_parameters_rejected(bad):
    kwargs = {"V": 60.0, "C": 60.0, "lam": 1 / 3600, "p_c": 0.0}
    kwargs.update(bad)
    with pytest.raises(ValueError):
        minimum_waste(**kwargs)
