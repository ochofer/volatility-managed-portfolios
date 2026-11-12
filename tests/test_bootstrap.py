"""Ledoit and Wolf's test: the same seed gives the same answer, the test rejects a true null at about its
nominal rate, its interval narrows with more months, its standard error agrees with the textbook formula
on independent normal returns, and the module loads on its own."""
from __future__ import annotations

import importlib.util
import pathlib
import statistics as st
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import bootstrap as B  # noqa: E402


def _pair(months, seed, shift=0.0):
    rng = np.random.default_rng(seed)
    r1, r2 = B.simulate_null_pair(months, 0.0065, 0.054, 0.6, 5, rng)
    return r1 + shift, r2


def test_the_module_loads_without_the_package():
    path = ROOT / "src" / "sq" / "bootstrap.py"
    assert "from ." not in path.read_text() and "import sq" not in path.read_text()
    spec = importlib.util.spec_from_file_location("lw_alone", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    r1, r2 = _pair(240, 1)
    assert mod.test(r1, r2, draws=199, seed=5) == B.test(r1, r2, draws=199, seed=5)


def test_same_seed_same_result_and_another_seed_another_interval():
    r1, r2 = _pair(480, 2)
    a, b = B.test(r1, r2, draws=499, seed=9), B.test(r1, r2, draws=499, seed=9)
    c = B.test(r1, r2, draws=499, seed=10)
    assert a == b
    assert c["difference"] == a["difference"] and c["se"] == a["se"] and c["critical"] != a["critical"]


def test_sharpe_difference_by_hand():
    r1 = np.array([0.02, -0.01, 0.03, 0.00])
    r2 = np.array([0.01, 0.01, -0.02, 0.02])
    sr = lambda r: st.mean(r) / st.pstdev(r)   # population standard deviation, as Ledoit and Wolf  # noqa: E731
    assert B.sharpe_difference(r1, r2) == pytest.approx(sr(list(r1)) - sr(list(r2)))


def test_standard_error_agrees_with_the_normal_formula_on_independent_returns():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((2, 20000))
    a, b = 0.01 + 0.05 * x[0], 0.008 + 0.05 * (0.6 * x[0] + 0.8 * x[1])
    m1, m2, s1, s2 = a.mean(), b.mean(), a.std(), b.std()
    s12 = np.cov(a, b, ddof=0)[0, 1]
    # Jobson and Korkie with Memmel's correction, the variance of s2 m1 - s1 m2, divided by (s1 s2)^2
    theta = (2 * s1**2 * s2**2 - 2 * s1 * s2 * s12 + 0.5 * m1**2 * s2**2 + 0.5 * m2**2 * s1**2
             - m1 * m2 / (s1 * s2) * s12**2) / len(a)
    assert B.standard_error(a, b) == pytest.approx(np.sqrt(theta) / (s1 * s2), rel=0.05)


def test_parzen_kernel_values():
    assert B._parzen(0) == 1 and B._parzen(0.5) == pytest.approx(0.25) and B._parzen(1) == 0 and B._parzen(1.5) == 0


def test_circular_blocks_wrap_past_the_last_month():
    rng = np.random.default_rng(0)
    idx = B.circular_block_indices(10, 4, 500, rng)
    assert idx.shape == (500, 8) and idx.min() == 0 and idx.max() == 9
    blocks = idx.reshape(500, 2, 4)
    assert np.all((np.diff(blocks, axis=2) % 10) == 1)          # consecutive months, 9 followed by 0


def test_rejects_a_true_null_at_about_the_nominal_rate():
    out = B.size_check(pairs=200, months=240, mean=0.0065, sd=0.054, rho=0.6, dof=5, seed=3, draws=299)
    # 200 pairs: two standard errors of a proportion of 0.05 is 0.031
    assert 0.01 <= out["rate"] <= 0.05 + 0.031 + 0.02


def test_interval_narrows_with_more_months():
    short = B.test(*_pair(240, 4), draws=499, seed=1)
    long = B.test(*_pair(960, 4), draws=499, seed=1)
    assert long["half_width"] < 0.7 * short["half_width"]


def test_a_large_true_difference_is_found():
    r1, r2 = _pair(960, 6, shift=0.02)          # S1's Sharpe ratio raised by about 0.37 a month
    out = B.test(r1, r2, draws=499, seed=2)
    assert out["excludes_zero"] and out["lower"] > 0 and out["p_value"] < 0.01
