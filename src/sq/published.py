"""
The published numbers of the three papers the study replicates, transcribed
from the journal PDFs, with the page and the table of every number.

The comparison tables in the notebooks are built from this module, never typed
into a notebook. tests/test_published.py re-reads every number from the
journal PDFs when they are present on the machine (they are copyrighted and
live outside the repository) and fails on any digit that differs.

Units are the papers' own: returns, alphas and standard deviations in per cent
a year, Sharpe and appraisal ratios annualised, leverage as a multiple of the
original factor. The keys are French's column names for the six factors
(MM print Mkt, SMB, HML, Mom, RMW, CMA; COWY print MKT, SMB, HML, MOM, RMW, CMA).
"""
from __future__ import annotations

import math

FACTORS = ("Mkt-RF", "SMB", "HML", "Mom", "RMW", "CMA")

# ---------------------------------------------------------------------------
# Moreira and Muir (2017), Journal of Finance 72(4), 1611-1644
# ---------------------------------------------------------------------------

# Table I, Panel A, p. 1619: f_sigma = alpha + beta f + e, univariate, monthly
# data with alpha and RMSE multiplied by 12; standard errors adjust for
# heteroskedasticity. The table's first six of ten columns.
MM_TABLE_I = {
    #          beta  (se)   alpha  (se)     N     R2    RMSE
    "Mkt-RF": (0.61, 0.05,  4.86, 1.56, 1065, 0.37, 51.39),
    "SMB":    (0.62, 0.08, -0.58, 0.91, 1065, 0.38, 30.44),
    "HML":    (0.57, 0.07,  1.97, 1.02, 1065, 0.32, 34.92),
    "Mom":    (0.47, 0.07, 12.51, 1.71, 1060, 0.22, 50.37),
    "RMW":    (0.62, 0.08,  2.44, 0.83,  621, 0.38, 20.16),
    "CMA":    (0.68, 0.05,  0.38, 0.67,  621, 0.46, 17.55),
}
MM_TABLE_I_FIELDS = ("beta", "beta_se", "alpha", "alpha_se", "N", "R2", "RMSE")

# Appraisal ratios printed in the text: the market's 0.34 and HML's 0.20 and
# profitability's 0.41 (p. 1620), and the market's 0.33 in the introduction
# (p. 1612). The figures E1 compares against are computed from Table I below.
MM_TEXT_APPRAISAL_P1620 = {"Mkt-RF": 0.34, "HML": 0.20, "RMW": 0.41}
MM_TEXT_APPRAISAL_P1612 = {"Mkt-RF": 0.33}

# Table IV, p. 1625: the market, "Realized variance" row. Average absolute
# change in monthly weight, expected return and alpha before costs (per cent a
# year), alpha after 1, 10 and 14 basis points of trading cost, and the
# break-even cost in basis points.
MM_TABLE_IV_MARKET = {
    "mean_abs_change_in_weight": 0.73,
    "expected_return": 9.47,
    "alpha": 4.86,
    "alpha_1bp": 4.77,
    "alpha_10bp": 3.98,
    "alpha_14bp": 3.63,
    "break_even_bp": 56,
}

# Table V, Panel A, p. 1626: the market, "Realized variance" row. Alpha and its
# standard error, Sharpe ratio, appraisal ratio, and percentiles of the weight
# c / RV.
MM_TABLE_V_MARKET = {
    "alpha": 4.86, "alpha_se": 1.56, "sharpe": 0.52, "appraisal": 0.34,
    "P50": 0.93, "P75": 1.59, "P90": 2.64, "P99": 6.39,
}


def mm_appraisal_from_table_i(factor: str) -> float:
    """alpha / RMSE times the square root of 12, from Table I (footnote 11, p. 1620)."""
    beta, beta_se, alpha, alpha_se, n, r2, rmse = MM_TABLE_I[factor]
    return alpha / rmse * math.sqrt(12)


# ---------------------------------------------------------------------------
# Cederburg, O'Doherty, Wang and Yan (2020), Journal of Financial Economics
# 138(1), 95-117. Their sample ends in December 2016 (Table 1 note, p. 99).
# ---------------------------------------------------------------------------

# Table 1, p. 99. Panel A, original factors, and Panel B, volatility-managed
# factors: mean, standard deviation (per cent a year) and Sharpe ratio.
COWY_TABLE_1_ORIGINAL = {
    #          mean    sd     SR
    "Mkt-RF": (7.80, 18.61, 0.42),
    "SMB":    (2.57, 11.12, 0.23),
    "HML":    (4.84, 12.14, 0.40),
    "Mom":    (7.94, 16.39, 0.48),
    "RMW":    (2.92,  7.71, 0.38),
    "CMA":    (3.72,  6.97, 0.53),
}
COWY_TABLE_1_MANAGED = {
    "Mkt-RF": (9.55, 18.61, 0.51),
    "SMB":    (0.86, 11.12, 0.08),
    "HML":    (4.64, 12.14, 0.38),
    "Mom":    (16.17, 16.39, 0.99),
    "RMW":    (3.94,  7.71, 0.51),
    "CMA":    (2.79,  6.97, 0.40),
}
# Panel C: Sharpe ratio difference, managed minus original, and the Jobson and
# Korkie p-value. Panel D: correlation with the original factor and the 1st,
# 50th and 99th percentiles of the weight c* / RV.
COWY_TABLE_1_DIFFERENCE = {
    "Mkt-RF": (0.09, 0.30), "SMB": (-0.15, 0.09), "HML": (-0.02, 0.86),
    "Mom": (0.50, 0.00), "RMW": (0.13, 0.29), "CMA": (-0.13, 0.23),
}
COWY_TABLE_1_PANEL_D = {
    #          corr   P01   P50   P99
    "Mkt-RF": (0.63, 0.04, 0.96, 6.47),
    "SMB":    (0.63, 0.03, 0.81, 5.07),
    "HML":    (0.57, 0.04, 1.02, 5.89),
    "Mom":    (0.48, 0.04, 1.01, 8.64),
    "RMW":    (0.59, 0.04, 1.11, 5.02),
    "CMA":    (0.68, 0.06, 0.97, 4.56),
}

# Table 3, Panel A.1, p. 104: the full-sample spanning regression. Alpha (per
# cent a year) with its t-statistic from White (1980) standard errors, beta with
# its t-statistic, adjusted R2, appraisal ratio; Panel A.2, the scaling constant c*.
COWY_TABLE_3 = {
    #          alpha  (t)    beta  (t)     R2    AR     c*
    "Mkt-RF": (4.63,  3.08, 0.63, 11.32, 0.40,  0.32, 10.33),
    "SMB":    (-0.76, -0.87, 0.63,  7.75, 0.40, -0.09,  2.63),
    "HML":    (1.87,  1.88, 0.57,  7.65, 0.33,  0.19,  2.95),
    "Mom":    (12.39, 7.31, 0.48,  7.13, 0.23,  0.86,  4.60),
    "RMW":    (2.23,  2.57, 0.59,  7.10, 0.34,  0.36,  1.48),
    "CMA":    (0.26,  0.39, 0.68, 13.82, 0.46,  0.05,  1.53),
}
COWY_TABLE_3_FIELDS = ("alpha", "alpha_t", "beta", "beta_t", "R2", "AR", "c")

# Table 5, Panel A, p. 106: the real-time strategies, K = 120, expanding
# window, gamma = 5, leverage at most 5; Sharpe ratios over the out-of-sample
# period, p-values of the differences in the second tuple (Jobson and Korkie).
COWY_TABLE_5 = {
    #          S1    S2    S1-S2  S3    S1-S3
    "Mkt-RF": (0.42, 0.46, -0.04, 0.53, -0.11),
    "SMB":    (0.14, 0.19, -0.06, 0.26, -0.12),
    "HML":    (0.38, 0.43, -0.06, 0.50, -0.12),
    "Mom":    (0.92, 0.49,  0.44, 0.99, -0.07),
    "RMW":    (0.44, 0.31,  0.13, 0.58, -0.14),
    "CMA":    (0.52, 0.56, -0.03, 0.64, -0.11),
}
COWY_TABLE_5_P = {
    #          S1-S2  S1-S3
    "Mkt-RF": (0.64, 0.01),
    "SMB":    (0.37, 0.14),
    "HML":    (0.41, 0.08),
    "Mom":    (0.00, 0.07),
    "RMW":    (0.53, 0.37),
    "CMA":    (0.20, 0.00),
}

# ---------------------------------------------------------------------------
# Barroso and Santa-Clara (2015), Journal of Financial Economics 116(1), 111-120.
# Sample 1927:03 to 2011:12.
# ---------------------------------------------------------------------------

BSC_FIELDS = ("max", "min", "mean", "sd", "kurtosis", "skewness", "sharpe")
# Table 1, p. 113, and Table 3, p. 116: monthly returns in per cent, mean and
# standard deviation annualised, excess kurtosis, skewness, annualised Sharpe ratio.
BSC_TABLE_1_WML = (26.18, -78.96, 14.46, 27.53, 18.24, -2.47, 0.53)
BSC_TABLE_3_WML = (26.18, -78.96, 14.46, 27.53, 18.24, -2.47, 0.53)
BSC_TABLE_3_WML_SCALED = (21.95, -28.40, 16.50, 16.95, 2.68, -0.42, 0.97)
BSC_TABLE_3_INFORMATION_RATIO = 0.78
# p. 112: maximum drawdown in per cent, unscaled and scaled.
BSC_MAX_DRAWDOWN = {"WML": -96.69, "WML scaled": -45.20}


def table(name: str):
    """One published table as a pandas DataFrame, factors as rows."""
    import pandas as pd
    if name == "mm_table_i":
        df = pd.DataFrame(MM_TABLE_I, index=MM_TABLE_I_FIELDS).T
        df["appraisal"] = [mm_appraisal_from_table_i(f) for f in df.index]
        return df
    if name == "cowy_table_1":
        o = pd.DataFrame(COWY_TABLE_1_ORIGINAL, index=["mean", "sd", "sharpe"]).T
        m = pd.DataFrame(COWY_TABLE_1_MANAGED, index=["mean", "sd", "sharpe"]).T
        d = pd.DataFrame(COWY_TABLE_1_DIFFERENCE, index=["difference", "p"]).T
        q = pd.DataFrame(COWY_TABLE_1_PANEL_D, index=["corr", "P01", "P50", "P99"]).T
        return pd.concat({"original": o, "managed": m, "difference": d, "weights": q}, axis=1)
    if name == "cowy_table_3":
        return pd.DataFrame(COWY_TABLE_3, index=COWY_TABLE_3_FIELDS).T
    if name == "cowy_table_5":
        s = pd.DataFrame(COWY_TABLE_5, index=["S1", "S2", "S1-S2", "S3", "S1-S3"]).T
        p = pd.DataFrame(COWY_TABLE_5_P, index=["p S1-S2", "p S1-S3"]).T
        return pd.concat([s, p], axis=1)
    if name == "bsc_table_3":
        return pd.DataFrame({"WML": BSC_TABLE_3_WML, "WML scaled": BSC_TABLE_3_WML_SCALED}, index=BSC_FIELDS).T
    raise KeyError(name)
