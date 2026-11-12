"""
The expectations judged, one function each, from the computed and the
published numbers. Each returns a table with one row per comparison and a
verdict that reads the levels from constants.py and nothing else.
"""
from __future__ import annotations

from statistics import NormalDist

import pandas as pd

from . import constants as C
from . import published as P

# The two-sided 5 per cent line for a t-statistic, from the normal distribution: 1.96.
Z_5 = NormalDist().inv_cdf(1 - C.SIGNIFICANCE_LEVEL / 2)


def e1(computed: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """E1 on Moreira and Muir's sample. `computed` has one row per factor with the columns of
    regression.table_i_row. Returns the comparison table, one row per factor, and whether E1 is met."""
    rows = []
    for f in C.FACTORS:
        beta, beta_se, alpha_p, se_p, n_p, r2_p, rmse_p = P.MM_TABLE_I[f]
        c = computed.loc[f]
        t_p = alpha_p / se_p
        t_c = c["alpha"] / c["alpha_se_white"]
        ar_p = P.mm_appraisal_from_table_i(f)
        row = {
            "factor": f,
            "alpha published": alpha_p, "alpha computed": c["alpha"],
            "se published": se_p, "se computed (White)": c["alpha_se_white"], "se computed (Newey-West)": c["alpha_se_nw"],
            "t published": t_p, "t computed (White)": t_c,
            "appraisal published": ar_p, "appraisal computed": c["appraisal"],
            "N published": n_p, "N computed": int(c["N"]),
            "sign matches": (alpha_p > 0) == (c["alpha"] > 0),
            "5% category matches": (abs(t_p) > Z_5) == (abs(t_c) > Z_5),
            "alpha within one published se": abs(c["alpha"] - alpha_p) <= C.E1_ALPHA_WITHIN_SE * se_p,
            "appraisal within 0.05": abs(c["appraisal"] - ar_p) <= C.E1_APPRAISAL_BAND,
        }
        legs = ["sign matches", "5% category matches", "alpha within one published se", "appraisal within 0.05"]
        if f == "Mkt-RF":
            row["Sharpe published (Table V)"] = P.MM_TABLE_V_MARKET["sharpe"]
            row["Sharpe computed"] = c["sharpe_managed"]
            row["Sharpe within 0.05"] = abs(c["sharpe_managed"] - P.MM_TABLE_V_MARKET["sharpe"]) <= C.E1_MARKET_SHARPE_BAND
            legs.append("Sharpe within 0.05")
        row["factor matches"] = all(row[leg] for leg in legs)
        rows.append(row)
    table = pd.DataFrame(rows).set_index("factor")
    met = int(table["factor matches"].sum()) >= C.E1_MIN_FACTORS
    return table, met


def _outside(computed: float, published: float, band: float) -> float:
    """How far a computed number lies outside the band around the published one (0 when inside)."""
    return max(0.0, abs(computed - published) - band)


def e2(computed: pd.DataFrame) -> tuple[pd.DataFrame, dict, bool]:
    """E2 on Cederburg et al.'s sample. `computed` has one row per factor and the columns sharpe_original,
    sharpe_managed (Table 1), s1, s2, s1_minus_s2, p_s1_s2, s3, s1_minus_s3 (Table 5, Panel A), Sharpe
    ratios annualised. Returns the comparison table (one row per factor, four comparisons each), the
    result of each clause (i) to (iv), and whether E2 is met: every clause must hold."""
    band, band_s3 = C.E2_SHARPE_BAND, C.E2_S1_S3_BAND
    rows = []
    for f in C.FACTORS:
        c = computed.loc[f]
        o_p, m_p = P.COWY_TABLE_1_ORIGINAL[f][2], P.COWY_TABLE_1_MANAGED[f][2]
        s1_p, s2_p, d12_p, s3_p, d13_p = P.COWY_TABLE_5[f]
        p12_p = P.COWY_TABLE_5_P[f][0]
        significant = c["p_s1_s2"] < C.SIGNIFICANCE_LEVEL
        row = {
            "factor": f,
            "original SR published": o_p, "original SR computed": c["sharpe_original"],
            "managed SR published": m_p, "managed SR computed": c["sharpe_managed"],
            "(i) both within 0.05": abs(c["sharpe_original"] - o_p) <= band and abs(c["sharpe_managed"] - m_p) <= band,
            "S1 published": s1_p, "S1 computed": c["s1"], "S2 published": s2_p, "S2 computed": c["s2"],
            "(ii) both within 0.05": abs(c["s1"] - s1_p) <= band and abs(c["s2"] - s2_p) <= band,
            "S1-S2 published": d12_p, "S1-S2 computed": c["s1_minus_s2"],
            "p published": p12_p, "p computed": c["p_s1_s2"],
            "sign matches": (d12_p > 0) == (c["s1_minus_s2"] > 0),
            "significant at 5%": significant,
            "significance as published": significant == (f in C.E2_ONLY_SIGNIFICANT),
            "S1-S3 published": d13_p, "S1-S3 computed": c["s1_minus_s3"],
            "(iv) within 0.05": abs(c["s1_minus_s3"] - d13_p) <= band_s3,
        }
        row["(iii) sign and significance as published"] = row["sign matches"] and row["significance as published"]
        row["comparisons holding"] = int(row["(i) both within 0.05"]) + int(row["(ii) both within 0.05"]) \
            + int(row["(iii) sign and significance as published"]) + int(row["(iv) within 0.05"])
        rows.append(row)
    table = pd.DataFrame(rows).set_index("factor")
    significant_set = set(table.index[table["significant at 5%"]])
    clauses = {
        "(i)": bool(table["(i) both within 0.05"].all()),
        "(ii)": bool(table["(ii) both within 0.05"].all()),
        "(iii)": int(table["sign matches"].sum()) >= C.E2_SIGN_MIN_FACTORS and significant_set == set(C.E2_ONLY_SIGNIFICANT),
        "(iv)": bool(table["(iv) within 0.05"].all()),
    }
    return table, clauses, all(clauses.values())


def e2_line(table: pd.DataFrame, clauses: dict) -> str:
    """The verdict of E2 in words, with the arithmetic beside each clause."""
    band = C.E2_SHARPE_BAND
    n_hold, n_all = int(table["comparisons holding"].sum()), 4 * len(table)
    met = all(clauses.values())
    parts = [f"E2: {'MET' if met else 'NOT MET'}. {n_hold} of {n_all} comparisons hold."]

    def misses(pairs):
        out = []
        for f in table.index:
            for label, comp, pub in pairs:
                c, p = table.loc[f, comp], table.loc[f, pub]
                gap = _outside(c, p, band)
                if gap > 0:
                    out.append(f"{f}'s {label} {c:.3f} against {p:.2f} published, {gap:.3f} outside the band of {band}")
        return out

    m1 = misses([("original Sharpe ratio", "original SR computed", "original SR published"),
                 ("managed Sharpe ratio", "managed SR computed", "managed SR published")])
    parts.append("(i) met: every original and managed Sharpe ratio within 0.05 of Table 1." if clauses["(i)"]
                 else "(i) not met: " + "; ".join(m1) + ".")
    m2 = misses([("S1", "S1 computed", "S1 published"), ("S2", "S2 computed", "S2 published")])
    parts.append("(ii) met: every S1 and S2 within 0.05 of Table 5." if clauses["(ii)"]
                 else "(ii) not met: " + "; ".join(m2) + ".")
    n_sign = int(table["sign matches"].sum())
    sig = ", ".join(table.index[table["significant at 5%"]]) or "none"
    parts.append(f"(iii) {'met' if clauses['(iii)'] else 'not met'}: the sign of S1 minus S2 matches for {n_sign} of "
                 f"{len(table)}, at least {C.E2_SIGN_MIN_FACTORS} required; significant at 5 per cent: {sig}; "
                 f"published: {', '.join(C.E2_ONLY_SIGNIFICANT)}.")
    off = [f for f in table.index if not table.loc[f, "(iv) within 0.05"]]
    parts.append("(iv) met: S1 minus S3 within 0.05 of Table 5 for all six." if clauses["(iv)"]
                 else "(iv) not met: S1 minus S3 outside 0.05 for " + ", ".join(off) + ".")
    return "\n".join(parts)


def e3(computed: dict) -> tuple[pd.DataFrame, bool]:
    """E3 on May 1927 to December 2011. `computed` holds the annualised Sharpe ratios sharpe_wml and
    sharpe_scaled and the maximum drawdowns mdd_wml and mdd_scaled as fractions (-0.5 a fall of half).
    Returns the comparison table, one row per series, and whether all four comparisons hold."""
    rows = []
    for name, sr_key, dd_key, sr_p in (("WML", "sharpe_wml", "mdd_wml", P.BSC_TABLE_3_WML[-1]),
                                       ("WML scaled", "sharpe_scaled", "mdd_scaled", P.BSC_TABLE_3_WML_SCALED[-1])):
        dd_p = P.BSC_MAX_DRAWDOWN[name]
        rows.append({
            "series": name,
            "Sharpe published": sr_p, "Sharpe computed": computed[sr_key],
            "Sharpe within 0.05": abs(computed[sr_key] - sr_p) <= C.E3_SHARPE_BAND,
            "maximum drawdown published (%)": dd_p, "maximum drawdown computed (%)": computed[dd_key] * 100,
            "drawdown within five points": abs(computed[dd_key] * 100 - dd_p) <= C.E3_DRAWDOWN_BAND * 100,
        })
    table = pd.DataFrame(rows).set_index("series")
    met = bool(table["Sharpe within 0.05"].all() and table["drawdown within five points"].all())
    return table, met


def e3_line(table: pd.DataFrame, met: bool) -> str:
    """The verdict of E3 in words, with the arithmetic beside each comparison."""
    n = int(table["Sharpe within 0.05"].sum() + table["drawdown within five points"].sum())
    w, s = table.loc["WML"], table.loc["WML scaled"]
    return (f"E3: {'MET' if met else 'NOT MET'}. {n} of 4 comparisons hold. "
            f"Sharpe ratios: WML {w['Sharpe computed']:.3f} against {w['Sharpe published']:.2f}, "
            f"scaled WML {s['Sharpe computed']:.3f} against {s['Sharpe published']:.2f}, band 0.05. "
            f"Maximum drawdowns: WML {w['maximum drawdown computed (%)']:.2f} against {w['maximum drawdown published (%)']:.2f} per cent, "
            f"scaled WML {s['maximum drawdown computed (%)']:.2f} against {s['maximum drawdown published (%)']:.2f} per cent, band five points.")
