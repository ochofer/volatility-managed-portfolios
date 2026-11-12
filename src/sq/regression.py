"""
The regression of a volatility-managed factor on its original factor, and the
measures the papers report from it.

    f_sigma_t = alpha + beta f_t + e_t, monthly, by ordinary least squares.

Two standard errors are computed for every coefficient:

  White (1980), the heteroskedasticity-robust standard error, which allows the
  size of e_t to change from month to month. Moreira and Muir's Table I and
  Cederburg et al.'s Table 3 use it (constants.SE_E1); E1 is judged with it.

  Newey and West (1987), which also allows e_t to be correlated with the
  previous L months' e, with weights 1 - l / (L + 1) on lag l (the Bartlett
  kernel), L = constants.NEWEY_WEST_LAGS. It is reported beside White's and is
  the one E4 to E6 use.

Neither applies a small-sample correction, which is the textbook form of both.

Units follow Moreira and Muir's tables (Table I note, p. 1619): alpha, its
standard error and the RMSE (the standard deviation of e) are multiplied by 12
and given in per cent a year; the appraisal ratio is alpha / RMSE times the
square root of 12 (footnote 11, p. 1620); Sharpe ratios are the monthly mean
over the monthly standard deviation times the square root of 12.

Two Sharpe ratios are compared with Jobson and Korkie's test, as Cederburg et
al. compare them (Table 1, p. 99, and Table 5, p. 106).

The maximum drawdown is the largest fall of compounded wealth from its highest
earlier level, as Barroso and Santa-Clara report it (p. 112).
"""
from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd

from . import constants as C


def ols(y: np.ndarray, x: np.ndarray, nw_lags: int = C.NEWEY_WEST_LAGS) -> dict:
    """Regression of y on a constant and x. Returns the coefficients, both standard errors, the residuals,
    N, R2 and the RMSE, all monthly and in decimals."""
    y = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones(len(y)), np.asarray(x, dtype=float)])
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    coef = xtx_inv @ X.T @ y
    e = y - X @ coef
    xe = X * e[:, None]                                  # row t is x_t e_t
    meat_white = xe.T @ xe
    meat_nw = meat_white.copy()
    for lag in range(1, nw_lags + 1):
        w = 1 - lag / (nw_lags + 1)
        g = xe[lag:].T @ xe[:-lag]
        meat_nw += w * (g + g.T)
    se_white = np.sqrt(np.diag(xtx_inv @ meat_white @ xtx_inv))
    se_nw = np.sqrt(np.diag(xtx_inv @ meat_nw @ xtx_inv))
    ss_res = float(e @ e)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return {
        "alpha": coef[0], "beta": coef[1],
        "alpha_se_white": se_white[0], "beta_se_white": se_white[1],
        "alpha_se_nw": se_nw[0], "beta_se_nw": se_nw[1],
        "residuals": e, "N": n, "R2": 1 - ss_res / ss_tot,
        "rmse": np.sqrt(ss_res / (n - k)),
    }


def sharpe(r: pd.Series | np.ndarray) -> float:
    """The annualised Sharpe ratio of a monthly excess return: mean over standard deviation times the
    square root of 12."""
    r = np.asarray(r, dtype=float)
    return float(r.mean() / r.std(ddof=1) * C.SHARPE_ANNUALISE)


def max_drawdown(r: pd.Series | np.ndarray) -> float:
    """The largest fall of wealth from its highest earlier level, as a fraction (-0.5 is a fall of half).
    Wealth starts at 1 and grows by (1 + r) each month, the return compounded, with nothing added for
    cash: the cumulative return of one dollar held in the strategy, as Barroso and Santa-Clara state
    theirs (p. 113)."""
    wealth = np.cumprod(1 + np.asarray(r, dtype=float))
    peak = np.maximum.accumulate(np.concatenate([[1.0], wealth]))[1:]
    return float((wealth / peak - 1).min())


def jobson_korkie(r_i: pd.Series | np.ndarray, r_j: pd.Series | np.ndarray) -> dict:
    """Jobson and Korkie's (1981) test that two return series over the same months have the same Sharpe
    ratio, with the correction of Memmel (2003), as Cederburg et al. write it (p. 99):

        z = (s_j m_i - s_i m_j) / sqrt(theta),
        theta = (1 / T) (2 s_i^2 s_j^2 - 2 s_i s_j s_ij + m_i^2 s_j^2 / 2 + m_j^2 s_i^2 / 2
                         - (m_i m_j / (s_i s_j)) s_ij^2),

    m the monthly means, s the monthly standard deviations, s_ij the covariance, T the months. z is
    compared with the normal distribution. Returns the annualised Sharpe ratio difference i minus j, z
    and the two-sided p-value."""
    r_i = np.asarray(r_i, dtype=float)
    r_j = np.asarray(r_j, dtype=float)
    if len(r_i) != len(r_j):
        raise ValueError("the two series must cover the same months")
    t = len(r_i)
    m_i, m_j = r_i.mean(), r_j.mean()
    s_i, s_j = r_i.std(ddof=1), r_j.std(ddof=1)
    s_ij = float(np.cov(r_i, r_j)[0, 1])
    theta = (2 * s_i**2 * s_j**2 - 2 * s_i * s_j * s_ij + 0.5 * m_i**2 * s_j**2 + 0.5 * m_j**2 * s_i**2
             - (m_i * m_j / (s_i * s_j)) * s_ij**2) / t
    z = (s_j * m_i - s_i * m_j) / np.sqrt(theta)
    p = 2 * (1 - NormalDist().cdf(abs(z)))
    return {"difference": (m_i / s_i - m_j / s_j) * C.SHARPE_ANNUALISE, "z": float(z), "p": float(p)}


def table_i_row(managed: pd.Series, original: pd.Series) -> dict:
    """One column of Moreira and Muir's Table I, in the paper's units, with both standard errors."""
    fit = ols(managed.to_numpy(), original.to_numpy())
    a = C.ALPHA_ANNUALISE * 100
    return {
        "beta": fit["beta"], "beta_se_white": fit["beta_se_white"],
        "alpha": fit["alpha"] * a, "alpha_se_white": fit["alpha_se_white"] * a, "alpha_se_nw": fit["alpha_se_nw"] * a,
        "N": fit["N"], "R2": fit["R2"], "RMSE": fit["rmse"] * a,
        "appraisal": fit["alpha"] / fit["rmse"] * C.SHARPE_ANNUALISE,
        "sharpe_managed": sharpe(managed), "sharpe_original": sharpe(original),
    }
