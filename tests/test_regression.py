"""The regression and its two standard errors, checked against numpy and, where it is installed, statsmodels."""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import regression as R  # noqa: E402


def _data(n=400, seed=3):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    e = rng.standard_normal(n) * (0.5 + np.abs(x))      # the noise grows with |x|, so White differs from the plain error
    e[1:] += 0.4 * e[:-1]                                # and neighbouring months are correlated, so Newey and West differs again
    return 0.3 + 0.7 * x + e, x


def test_coefficients_match_least_squares():
    y, x = _data()
    fit = R.ols(y, x)
    X = np.column_stack([np.ones_like(x), x])
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    assert fit["alpha"] == pytest.approx(coef[0]) and fit["beta"] == pytest.approx(coef[1])
    assert fit["N"] == 400 and fit["rmse"] == pytest.approx(np.sqrt((fit["residuals"] ** 2).sum() / 398))


def test_newey_west_with_no_lags_is_white():
    y, x = _data()
    fit = R.ols(y, x, nw_lags=0)
    assert fit["alpha_se_nw"] == pytest.approx(fit["alpha_se_white"])


def test_white_by_hand_on_four_points():
    # y = [1, 2, 2, 5] on x = [0, 1, 2, 3]: the slope is 6 / 5 = 1.2, the intercept 2.5 - 1.2 * 1.5 = 0.7, residuals 0.3, 0.1, -1.1, 0.7
    fit = R.ols(np.array([1.0, 2.0, 2.0, 5.0]), np.array([0.0, 1.0, 2.0, 3.0]), nw_lags=0)
    assert fit["alpha"] == pytest.approx(0.7) and fit["beta"] == pytest.approx(1.2)
    X = np.array([[1, 0], [1, 1], [1, 2], [1, 3]], dtype=float)
    e = np.array([0.3, 0.1, -1.1, 0.7])
    inv = np.linalg.inv(X.T @ X)
    v = inv @ (X.T * e ** 2) @ X @ inv
    assert fit["alpha_se_white"] == pytest.approx(np.sqrt(v[0, 0]))


def test_against_statsmodels_when_installed():
    sm = pytest.importorskip("statsmodels.api")
    y, x = _data()
    X = sm.add_constant(x)
    white = sm.OLS(y, X).fit(cov_type="HC0")
    nw = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 12, "use_correction": False})
    fit = R.ols(y, x, nw_lags=12)
    assert fit["alpha_se_white"] == pytest.approx(white.bse[0]) and fit["beta_se_white"] == pytest.approx(white.bse[1])
    assert fit["alpha_se_nw"] == pytest.approx(nw.bse[0]) and fit["beta_se_nw"] == pytest.approx(nw.bse[1])
    assert fit["R2"] == pytest.approx(white.rsquared)


def test_table_i_units():
    y, x = _data()
    row = R.table_i_row(pd.Series(y / 100), pd.Series(x / 100))
    fit = R.ols(y / 100, x / 100)
    assert row["alpha"] == pytest.approx(fit["alpha"] * 1200)
    assert row["RMSE"] == pytest.approx(fit["rmse"] * 1200)
    assert row["appraisal"] == pytest.approx(row["alpha"] / row["RMSE"] * np.sqrt(12))
    assert row["sharpe_managed"] == pytest.approx((y / 100).mean() / (y / 100).std(ddof=1) * np.sqrt(12))


def test_jobson_korkie_against_the_formula_in_plain_python():
    # Cederburg et al., p. 99, with Memmel's correction, written out with the standard library only.
    import statistics as st
    from math import sqrt
    from statistics import NormalDist
    a = [0.02, 0.00, 0.04, 0.02, -0.01, 0.03]
    b = [0.01, 0.01, 0.03, -0.01, 0.00, 0.02]
    T = len(a)
    mi, mj, si, sj = st.mean(a), st.mean(b), st.stdev(a), st.stdev(b)
    sij = st.covariance(a, b)
    theta = (2 * si**2 * sj**2 - 2 * si * sj * sij + mi**2 * sj**2 / 2 + mj**2 * si**2 / 2 - mi * mj / (si * sj) * sij**2) / T
    z = (sj * mi - si * mj) / sqrt(theta)
    out = R.jobson_korkie(np.array(a), np.array(b))
    assert out["z"] == pytest.approx(z)
    assert out["p"] == pytest.approx(2 * (1 - NormalDist().cdf(abs(z))))
    assert out["difference"] == pytest.approx((mi / si - mj / sj) * np.sqrt(12))


def test_jobson_korkie_is_antisymmetric_and_ignores_scale():
    y, x = _data()
    a, b = y / 100, (x + 0.2) / 100
    ab, ba = R.jobson_korkie(a, b), R.jobson_korkie(b, a)
    assert ab["z"] == pytest.approx(-ba["z"]) and ab["p"] == pytest.approx(ba["p"])
    scaled = R.jobson_korkie(3 * a, 0.5 * b)            # a Sharpe ratio does not change with a positive multiple
    assert scaled["z"] == pytest.approx(ab["z"]) and scaled["difference"] == pytest.approx(ab["difference"])


def test_max_drawdown_by_hand():
    # wealth 1.1, 0.88, 0.968, 1.2584: the peak 1.1 falls to 0.88, a drawdown of 0.2
    assert R.max_drawdown(np.array([0.10, -0.20, 0.10, 0.30])) == pytest.approx(-0.2)
    # a fall from the start counts against the starting wealth of 1
    assert R.max_drawdown(np.array([-0.5, 0.2])) == pytest.approx(-0.5)
    assert R.max_drawdown(np.array([0.01, 0.02])) == 0.0
