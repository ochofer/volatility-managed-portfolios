"""The verdicts: computed numbers equal to the published ones meet each expectation, and one number moved
past its level breaks the clause that reads it, and only that clause."""
from __future__ import annotations

import pathlib
import sys

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import constants as C  # noqa: E402
from sq import published as P  # noqa: E402
from sq import verdicts as V  # noqa: E402


def _e1_as_published():
    rows = {}
    for f in C.FACTORS:
        beta, beta_se, alpha, se, n, r2, rmse = P.MM_TABLE_I[f]
        rows[f] = {"alpha": alpha, "alpha_se_white": se, "alpha_se_nw": se, "appraisal": P.mm_appraisal_from_table_i(f),
                   "N": n, "sharpe_managed": P.MM_TABLE_V_MARKET["sharpe"]}
    return pd.DataFrame(rows).T


def _e2_as_published():
    rows = {}
    for f in C.FACTORS:
        s1, s2, d12, s3, d13 = P.COWY_TABLE_5[f]
        rows[f] = {"sharpe_original": P.COWY_TABLE_1_ORIGINAL[f][2], "sharpe_managed": P.COWY_TABLE_1_MANAGED[f][2],
                   "s1": s1, "s2": s2, "s1_minus_s2": d12, "p_s1_s2": P.COWY_TABLE_5_P[f][0], "s3": s3, "s1_minus_s3": d13}
    return pd.DataFrame(rows).T


def test_e1_as_published_is_met_and_one_factor_may_miss():
    table, met = V.e1(_e1_as_published())
    assert met and table["factor matches"].all()
    moved = _e1_as_published()
    moved.loc["SMB", "alpha"] = 5.0                     # the sign flips and the alpha leaves its standard error
    table, met = V.e1(moved)
    assert met and not table.loc["SMB", "factor matches"] and table["factor matches"].sum() == 5


def test_e2_as_published_is_met():
    table, clauses, met = V.e2(_e2_as_published())
    assert met and all(clauses.values()) and table["comparisons holding"].sum() == 24
    assert V.e2_line(table, clauses).startswith("E2: MET. 24 of 24 comparisons hold.")


def test_e2_one_managed_sharpe_ratio_outside_the_band_breaks_clause_i_only():
    moved = _e2_as_published()
    moved.loc["RMW", "sharpe_managed"] += 0.056
    table, clauses, met = V.e2(moved)
    assert not met and clauses == {"(i)": False, "(ii)": True, "(iii)": True, "(iv)": True}
    line = V.e2_line(table, clauses)
    assert "E2: NOT MET. 23 of 24" in line and "RMW's managed Sharpe ratio 0.566 against 0.51 published, 0.006 outside" in line


def test_e2_clause_iii_reads_the_signs_and_the_significance():
    moved = _e2_as_published()
    moved.loc[["Mkt-RF", "SMB"], "s1_minus_s2"] *= -1   # two signs flip: four of six, five required
    assert V.e2(moved)[1]["(iii)"] is False
    moved = _e2_as_published()
    moved.loc["SMB", "p_s1_s2"] = 0.01                  # a second significant difference
    assert V.e2(moved)[1]["(iii)"] is False
    moved = _e2_as_published()
    moved.loc["Mkt-RF", "s1_minus_s2"] *= -1            # one sign flips: five of six still holds
    assert V.e2(moved)[1]["(iii)"] is True


def test_e3_as_published_is_met_and_reads_both_bands():
    as_published = {"sharpe_wml": P.BSC_TABLE_3_WML[-1], "sharpe_scaled": P.BSC_TABLE_3_WML_SCALED[-1],
                    "mdd_wml": P.BSC_MAX_DRAWDOWN["WML"] / 100, "mdd_scaled": P.BSC_MAX_DRAWDOWN["WML scaled"] / 100}
    table, met = V.e3(as_published)
    assert met and V.e3_line(table, met).startswith("E3: MET. 4 of 4 comparisons hold.")
    moved = dict(as_published, mdd_scaled=as_published["mdd_scaled"] - 0.051)    # 5.1 points deeper
    table, met = V.e3(moved)
    assert not met and not table.loc["WML scaled", "drawdown within five points"] and table["Sharpe within 0.05"].all()


def test_e4_reads_signs_and_significance_strictly_and_counts_categories_beside():
    factors = pd.DataFrame({
        "alpha":         [4.9, -0.6, 1.7, 12.8, 2.8, 0.4],
        "t_nw":          [2.8, -0.4, 1.4, 6.2, 2.8, 0.7],
        "difference":    [0.10, -0.14, -0.04, 0.51, 0.19, -0.12],
        "excludes_zero": [False, False, False, True, True, False],
    }, index=list(C.FACTORS))
    table, parts, met = V.e4(0.05, factors)
    # HML and CMA: positive alpha, negative difference, both not significant: they fail the strict reading only
    assert list(table.index[~table["counts (strict)"]]) == ["Mkt-RF", "HML", "CMA"]
    assert parts["count strict"] == 3 and parts["count by category"] == 5 and parts["size"] and not met
    assert not V.e4(0.03, factors)[1]["size"]


def test_e5_counts_and_the_median_clause():
    res = pd.DataFrame({"difference": [-0.1, 0.2, 0.05, 0.4, -0.2, 0.0], "lower": [-0.3, 0.01, -0.2, 0.1, -0.5, -0.3],
                        "upper": [0.1, 0.39, 0.3, 0.7, 0.1, 0.3], "half_width": [0.2, 0.19, 0.25, 0.3, 0.3, 0.3]},
                       index=list(C.FACTORS))
    counts, met = V.e5(res)
    assert counts["count above"] == 2 and counts["median difference"] == pytest.approx(0.025)
    assert counts["median half-width"] == pytest.approx(0.275) and counts["median within"] and met
    res.loc["CMA", "lower"] = 0.01
    assert not V.e5(res)[1]


def test_e6_as_published_is_met_and_one_percentile_can_break_it():
    market_net = {"alpha": P.MM_TABLE_IV_MARKET["alpha_10bp"], "se_nw": 1.7}
    market_pct = {f"P{q}": P.MM_TABLE_V_MARKET[f"P{q}"] for q in C.E6_MARKET_PERCENTILES}
    cowy_pct = pd.DataFrame({f: {"P50": P.COWY_TABLE_1_PANEL_D[f][2], "P99": P.COWY_TABLE_1_PANEL_D[f][3]} for f in C.FACTORS}).T
    table, met = V.e6(market_net, market_pct, cowy_pct)
    assert met and len(table) == 17
    market_pct["P99"] += 1.01
    assert not V.e6(market_net, market_pct, cowy_pct)[1]
