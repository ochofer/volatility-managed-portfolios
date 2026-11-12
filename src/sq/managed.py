"""
The signal and the two constructions built on it.

The signal is last month's realised variance of a factor, computed from the
factor's daily returns. Each paper defines it in its own way, and each
comparison with a paper's printed numbers uses that paper's definition
(constants.RV_BY_COMPARISON):

  rv_mm     Moreira and Muir, equation 2, p. 1616: each day's return minus the
            month's mean daily return, squared and summed over the month.
  rv_cowy   Cederburg, O'Doherty, Wang and Yan, equation 4, p. 98: 22 divided
            by the month's number of trading days J, times the sum of squared
            daily returns.
  rv_bsc    Barroso and Santa-Clara, equation 5, p. 115: 21 times the mean
            squared daily return over the last 126 trading days up to the
            month's last trading day.

The volatility-managed factor (Moreira and Muir, equation 1, p. 1616) holds
c / RV_{t-1} units of the factor in month t, with c set so that the managed
and the original factor have the same standard deviation over the sample.

The real-time combination (Cederburg et al., section 4.3, pp. 106-107) mixes
the volatility-managed and the original factor with mean-variance weights
estimated each month from the months before it only. Its position in the
original factor is y_t = x_sigma c_t / RV_{t-1} + x, truncated at plus or
minus the cap (p. 107: "a leverage constraint of |y_t| <= 5"). The ex post
optimal combination (Table 5, p. 106) holds one pair of weights, set with the
means and the covariance of the same months it is applied to.

Barroso and Santa-Clara's scaled momentum (equation 6, p. 115) holds WML at a
weight of a 12 per cent target volatility over the volatility of the last 126
trading days.

All returns are monthly decimal excess returns indexed by a monthly Period;
daily returns are indexed by a daily Period.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import constants as C


# ---------------------------------------------------------------------------
# The signal
# ---------------------------------------------------------------------------

def _by_month(daily: pd.Series):
    daily = daily.dropna()
    return daily.groupby(daily.index.asfreq("M"))


def rv_mm(daily: pd.Series) -> pd.Series:
    """Moreira and Muir's realised variance of each calendar month (equation 2)."""
    return _by_month(daily).apply(lambda r: float(((r - r.mean()) ** 2).sum())).rename("rv_mm")


def rv_cowy(daily: pd.Series) -> pd.Series:
    """Cederburg et al.'s realised variance of each calendar month (equation 4): 22 / J times the sum of squares."""
    g = _by_month(daily)
    return (C.RV_COWY_DAYS * g.apply(lambda r: float((r ** 2).sum())) / g.size()).rename("rv_cowy")


def rv_bsc(daily: pd.Series) -> pd.Series:
    """Barroso and Santa-Clara's variance at each month's last trading day (equation 5): 21 times the mean
    squared daily return over the last 126 trading days. NaN until 126 trading days are available."""
    daily = daily.dropna()
    mean_sq = (daily ** 2).rolling(C.RV_BSC_TRADING_DAYS, min_periods=C.RV_BSC_TRADING_DAYS).mean()
    month_end = mean_sq.groupby(mean_sq.index.asfreq("M")).last()
    return (C.RV_BSC_DAYS_PER_MONTH * month_end).rename("rv_bsc")


def lagged(rv: pd.Series) -> pd.Series:
    """The variance of month t-1 indexed at month t, the value a position for month t can use."""
    out = rv.copy()
    out.index = out.index + 1
    return out.rename(f"{rv.name}_lag")


# ---------------------------------------------------------------------------
# The volatility-managed factor
# ---------------------------------------------------------------------------

def volatility_managed(f: pd.Series, rv: pd.Series, start: str, end: str, c: float | None = None):
    """The volatility-managed factor on the months start to end.

    Returns (frame, c). The frame has one row per month with the factor's return f, last month's variance
    rv_lag, the position weight = c / rv_lag and the managed return = weight * f. With c None, c is set so
    that the managed and the original return have the same standard deviation over these months (Moreira
    and Muir, p. 1616); a given c is used as it is, for months after the sample c was set on.
    """
    df = pd.DataFrame({"f": f, "rv_lag": lagged(rv)}).loc[start:end].dropna()
    raw = df["f"] / df["rv_lag"]
    if c is None:
        c = float(df["f"].std() / raw.std())
    df["weight"] = c / df["rv_lag"]
    df["managed"] = df["weight"] * df["f"]
    return df, c


# ---------------------------------------------------------------------------
# The real-time combination
# ---------------------------------------------------------------------------

def mean_variance_weights(returns: np.ndarray, gamma: float) -> np.ndarray:
    """(1 / gamma) Sigma^-1 mu for the columns of `returns` (months in rows), with the sample covariance."""
    mu = returns.mean(axis=0)
    sigma = np.atleast_2d(np.cov(returns, rowvar=False))
    return np.linalg.solve(sigma, mu) / gamma


def real_time(f: pd.Series, rv: pd.Series, first: str, end: str, k: int = C.REALTIME_K,
              gamma: float = C.REALTIME_GAMMA, cap: float = C.REALTIME_LEVERAGE_CAP) -> pd.DataFrame:
    """Cederburg et al.'s real-time combination (S1) and real-time original (S2), month by month.

    The months run from `first` to `end`; the first k are the initial training period and carry no
    position. For each later month t the window is every month from `first` to t-1 (an expanding window):

      1. c_t gives the managed and the original factor the same variance over the window;
      2. the means and the covariance of the managed and the original factor over the window give the
         weights (x_sigma, x) = (1 / gamma) Sigma^-1 mu;
      3. the position in the original factor is y_t = x_sigma c_t / RV_{t-1} + x, truncated at +-cap;
      4. S1's return is y_t f_t.

    S2 holds y2_t = (1 / gamma) mu_f / sigma_f^2 of the original factor alone, under the same cap, and
    returns y2_t f_t. Nothing from month t or later enters month t's positions.
    """
    df = pd.DataFrame({"f": f, "rv_lag": lagged(rv)}).loc[first:end].dropna()
    fr = df["f"].to_numpy()
    rv_lag = df["rv_lag"].to_numpy()
    raw = fr / rv_lag
    rows = []
    for i in range(k, len(df)):
        f_win, raw_win = fr[:i], raw[:i]
        c_t = f_win.std(ddof=1) / raw_win.std(ddof=1)
        x_sigma, x = mean_variance_weights(np.column_stack([c_t * raw_win, f_win]), gamma)
        y = x_sigma * c_t / rv_lag[i] + x
        y_capped = float(np.clip(y, -cap, cap))
        y2 = float(np.clip(f_win.mean() / (gamma * f_win.var(ddof=1)), -cap, cap))
        rows.append({
            "month": df.index[i], "window": i, "c": c_t, "x_sigma": x_sigma, "x": x,
            "y_uncapped": y, "y": y_capped, "at_cap": abs(y) > cap,
            "f": fr[i], "s1": y_capped * fr[i], "y2": y2, "s2": y2 * fr[i],
        })
    out = pd.DataFrame(rows).set_index("month")
    out.index = pd.PeriodIndex(out.index, freq="M")
    return out


def ex_post_combination(managed: pd.Series, original: pd.Series, gamma: float = C.REALTIME_GAMMA):
    """Cederburg et al.'s ex post optimal combination, S3 (Table 5, p. 106): one pair of weights
    (x_sigma, x) = (1 / gamma) Sigma^-1 mu from the means and the covariance of the managed and the
    original factor over the months given, held in every one of those months. The weights use the
    months they are applied to, which no investor could have done. No cap is applied: the Table 5 note
    limits the sum of the absolute weights on the two factors to 5, and gamma = 5 keeps these weights
    far below it. The scale of the managed factor (its c) changes x_sigma and leaves the returns as
    they are. Returns (the monthly return series, the weights)."""
    both = pd.concat([managed.rename("managed"), original.rename("original")], axis=1).dropna()
    w = mean_variance_weights(both.to_numpy(), gamma)
    return pd.Series(both.to_numpy() @ w, index=both.index, name="s3"), w


def scaled_momentum(wml: pd.Series, rv: pd.Series, start: str, end: str,
                    target: float = C.BSC_TARGET_VOL_MONTHLY) -> pd.DataFrame:
    """Barroso and Santa-Clara's scaled momentum (equation 6, p. 115) on the months start to end: WML
    times target / sigma_hat, sigma_hat the square root of the variance of equation 5 at the end of the
    month before (rv_bsc, lagged one month), target the monthly volatility of 12 per cent a year. The
    frame holds WML, sigma_hat, the weight target / sigma_hat and the scaled return."""
    sigma = np.sqrt(lagged(rv)).rename("sigma_hat")
    df = pd.concat([wml.rename("wml"), sigma], axis=1).loc[start:end].dropna()
    df["weight"] = target / df["sigma_hat"]
    df["scaled"] = df["weight"] * df["wml"]
    return df


def turnover(position: pd.Series) -> pd.Series:
    """The position's turnover each month: the absolute change from the month before, |w_t - w_(t-1)|.
    The first month carries none. The factor's own trading is the same for the managed and the original
    factor and is left out of both."""
    return position.diff().abs().fillna(0.0).rename("turnover")


def net_of_cost(managed: pd.Series, position: pd.Series, cost: float = C.COST_PER_TURNOVER) -> pd.Series:
    """The managed return less `cost` per unit of the position's turnover in the month (Moreira and Muir,
    Table IV, p. 1625)."""
    return (managed - cost * turnover(position)).rename("net")


def percentiles(s: pd.Series, levels=(5, 50, 95)) -> dict:
    """The given percentiles of a series and its maximum, keyed P5, P50, ..., max."""
    out = {f"P{p}": float(np.percentile(s.dropna(), p)) for p in levels}
    out["max"] = float(s.max())
    return out
