"""The realised variance and the two constructions, checked on small series whose answers are worked by hand."""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import constants as C  # noqa: E402
from sq import managed as M  # noqa: E402


def _daily(values: dict) -> pd.Series:
    idx = pd.PeriodIndex(list(values), freq="D")
    return pd.Series(list(values.values()), index=idx, dtype=float)


# One month of three trading days and one month of two, worked by hand:
# January: 0.01, -0.02, 0.03; mean 0.02/3; squared deviations sum to 0.0014 - 3 * (0.02/3)**2 = 0.00126667.
# February: 0.01, 0.01; mean 0.01; squared deviations 0.
DAYS = _daily({"2000-01-03": 0.01, "2000-01-04": -0.02, "2000-01-05": 0.03, "2000-02-01": 0.01, "2000-02-02": 0.01})


def test_rv_mm_is_the_sum_of_squared_deviations_from_the_month_mean():
    rv = M.rv_mm(DAYS)
    assert rv.loc["2000-01"] == pytest.approx(0.0014 - 3 * (0.02 / 3) ** 2)
    assert rv.loc["2000-02"] == pytest.approx(0.0)


def test_rv_cowy_rescales_the_sum_of_squares_to_22_days():
    rv = M.rv_cowy(DAYS)
    assert rv.loc["2000-01"] == pytest.approx(22 / 3 * 0.0014)
    assert rv.loc["2000-02"] == pytest.approx(22 / 2 * 0.0002)


def test_rv_bsc_needs_126_days_and_is_a_monthly_variance():
    idx = pd.period_range("2001-01-01", periods=200, freq="D")
    daily = pd.Series(0.01, index=idx)
    rv = M.rv_bsc(daily)
    # 126 days are reached on 6 May 2001, so April has no value and May has one
    assert np.isnan(rv.loc["2001-04"]) and rv.loc["2001-05"] == pytest.approx(21 * 0.0001)


def test_lag_puts_last_months_variance_on_this_month():
    rv = pd.Series([1.0, 2.0], index=pd.PeriodIndex(["2000-01", "2000-02"], freq="M"), name="rv_mm")
    lag = M.lagged(rv)
    assert str(lag.index[0]) == "2000-02" and lag.loc["2000-02"] == 1.0


def _monthly(n: int, seed: int = 1):
    rng = np.random.default_rng(seed)
    idx = pd.period_range("1990-01", periods=n, freq="M")
    f = pd.Series(0.005 + 0.04 * rng.standard_normal(n), index=idx)
    rv = pd.Series(0.0005 + 0.002 * rng.random(n), index=idx, name="rv")
    return f, rv


def test_volatility_managed_equalises_the_standard_deviation_and_uses_the_lag():
    f, rv = _monthly(60)
    df, c = M.volatility_managed(f, rv, "1990-02", "1994-12")
    assert len(df) == 59
    assert df["managed"].std() == pytest.approx(df["f"].std())
    t = pd.Period("1993-06", "M")
    assert df.loc[t, "weight"] == pytest.approx(c / rv.loc[t - 1])
    assert df.loc[t, "managed"] == pytest.approx(c / rv.loc[t - 1] * f.loc[t])
    # a given c is used as it is
    df2, c2 = M.volatility_managed(f, rv, "1990-02", "1994-12", c=1.0)
    assert c2 == 1.0 and df2.loc[t, "weight"] == pytest.approx(1 / rv.loc[t - 1])


def test_real_time_on_one_month_worked_with_numpy():
    f, rv = _monthly(80)
    out = M.real_time(f, rv, "1990-02", "1996-08", k=24, gamma=5.0, cap=5.0)
    t = pd.Period("1993-01", "M")                         # the 36th month from 1990-02, so 35 months in its window
    win = pd.period_range("1990-02", "1992-12", freq="M")
    fw = f.loc[win].to_numpy()
    raw = fw / rv.loc[win - 1].to_numpy()
    c_t = fw.std(ddof=1) / raw.std(ddof=1)
    X = np.column_stack([c_t * raw, fw])
    xs, x = np.linalg.solve(np.cov(X, rowvar=False), X.mean(axis=0)) / 5.0
    y = np.clip(xs * c_t / rv.loc[t - 1] + x, -5, 5)
    row = out.loc[t]
    assert row["window"] == 35 and row["c"] == pytest.approx(c_t)
    assert row["y"] == pytest.approx(y) and row["s1"] == pytest.approx(y * f.loc[t])
    y2 = np.clip(fw.mean() / (5.0 * fw.var(ddof=1)), -5, 5)
    assert row["y2"] == pytest.approx(y2) and row["s2"] == pytest.approx(y2 * f.loc[t])
    assert str(out.index[0]) == "1992-02"                # the first 24 months carry no position


def test_real_time_uses_no_month_from_t_on_and_the_position_does_not_depend_on_c():
    f, rv = _monthly(80)
    base = M.real_time(f, rv, "1990-02", "1996-08", k=24)
    g = f.copy()
    g.loc["1994-01":] = g.loc["1994-01":] * 10           # change the future
    moved = M.real_time(g, rv, "1990-02", "1996-08", k=24)
    t = pd.Period("1994-01", "M")
    assert moved.loc[t, "y"] == pytest.approx(base.loc[t, "y"])
    assert moved.loc[t, "y2"] == pytest.approx(base.loc[t, "y2"])
    # Scaling the managed factor by any constant changes x_sigma by its inverse, so y_t does not depend on c_t.
    fw = f.loc["1990-02":"1993-12"].to_numpy()
    raw = fw / rv.loc[pd.period_range("1990-01", "1993-11", freq="M")].to_numpy()
    for c in (1.0, 7.0):
        xs, x = M.mean_variance_weights(np.column_stack([c * raw, fw]), 5.0)
        assert xs * c == pytest.approx(base.loc[t, "x_sigma"] * base.loc[t, "c"])


def test_the_cap_truncates_the_position():
    idx = pd.period_range("1990-01", periods=40, freq="M")
    f = pd.Series(np.where(np.arange(40) % 2 == 0, 0.05, 0.04), index=idx)   # high mean, low variance
    rv = pd.Series(np.where(np.arange(40) % 3 == 0, 0.0010, 0.0012), index=idx, name="rv")   # varies, so the two series are not collinear
    out = M.real_time(f, rv, "1990-02", "1993-04", k=12)
    assert (out["y"].abs() <= C.REALTIME_LEVERAGE_CAP + 1e-12).all() and out["at_cap"].any()
    assert (out["y2"].abs() <= C.REALTIME_LEVERAGE_CAP + 1e-12).all()
