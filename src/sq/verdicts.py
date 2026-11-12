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


def e5_counts(results: pd.DataFrame) -> dict:
    """The two counts E5 reads, from one row per factor with the annualised Sharpe ratio difference and its
    bootstrap interval (columns difference, lower, upper, half_width): the factors whose interval lies above
    zero, and whether the median difference lies within plus or minus the median half-width."""
    above = list(results.index[results["lower"] > 0])
    median_difference = float(results["difference"].median())
    median_half_width = float(results["half_width"].median())
    return {"factors above": above, "count above": len(above),
            "median difference": median_difference, "median half-width": median_half_width,
            "median within": abs(median_difference) <= median_half_width}


def e5(real_time: pd.DataFrame) -> tuple[dict, bool]:
    """E5 on the months after Moreira and Muir's sample: the real-time combination against the real-time
    original, one row per factor. Met when at most E5_MAX_FACTORS_ABOVE intervals lie above zero and the
    median difference lies within the median half-width."""
    counts = e5_counts(real_time)
    met = counts["count above"] <= C.E5_MAX_FACTORS_ABOVE and counts["median within"]
    return counts, met


def e5_line(counts: dict, met: bool, managed: dict | None = None) -> str:
    """The verdict of E5 in words, with the counts of the volatility-managed factor beside it, in no verdict."""
    above = ", ".join(counts["factors above"]) or "none"
    text = (f"E5: {'MET' if met else 'NOT MET'}. The real-time combination's Sharpe ratio exceeds S2's by more than "
            f"the interval allows on {counts['count above']} of 6 factors ({above}), at most "
            f"{C.E5_MAX_FACTORS_ABOVE} allowed; the median difference, {counts['median difference']:+.3f}, lies "
            f"{'within' if counts['median within'] else 'outside'} plus or minus the median half-width, "
            f"{counts['median half-width']:.3f}.")
    if managed is not None:
        m_above = ", ".join(managed["factors above"]) or "none"
        text += (f" In no verdict, the volatility-managed factor against the original: above on "
                 f"{managed['count above']} of 6 ({m_above}); median difference {managed['median difference']:+.3f}, "
                 f"{'within' if managed['median within'] else 'outside'} the median half-width, "
                 f"{managed['median half-width']:.3f}.")
    return text


def e6(market_net: dict, market_percentiles: dict, cowy_percentiles: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """E6. `market_net` holds the market's volatility-managed alpha net of the base cost and its Newey-West
    standard error, both in per cent a year, on Moreira and Muir's sample. `market_percentiles` holds the
    market's P50, P75, P90 and P99 of the position there. `cowy_percentiles` has one row per factor with
    P50 and P99 of the position on Cederburg et al.'s sample. Returns one row per comparison and whether
    all hold."""
    rows = []
    t = market_net["alpha"] / market_net["se_nw"]
    rows.append({"comparison": "Mkt-RF alpha net of 10 bp, Moreira and Muir's sample", "published": P.MM_TABLE_IV_MARKET["alpha_10bp"],
                 "computed": market_net["alpha"], "level": f"positive and t above {C.E6_MIN_NW_T}",
                 "holds": market_net["alpha"] > 0 and t > C.E6_MIN_NW_T, "detail": f"Newey-West t {t:.2f}"})
    for q in C.E6_MARKET_PERCENTILES:
        band = C.E6_P99_BAND if q == 99 else C.E6_PERCENTILE_BAND
        pub = P.MM_TABLE_V_MARKET[f"P{q}"]
        comp = market_percentiles[f"P{q}"]
        rows.append({"comparison": f"Mkt-RF position P{q}, Moreira and Muir's sample", "published": pub, "computed": comp,
                     "level": f"within {band}", "holds": abs(comp - pub) <= band, "detail": ""})
    for f in C.FACTORS:
        corr, p01, p50, p99 = P.COWY_TABLE_1_PANEL_D[f]
        for label, pub, band in (("P50", p50, C.E6_PERCENTILE_BAND), ("P99", p99, C.E6_P99_BAND)):
            comp = float(cowy_percentiles.loc[f, label])
            rows.append({"comparison": f"{f} position {label}, Cederburg et al.'s sample", "published": pub, "computed": comp,
                         "level": f"within {band}", "holds": abs(comp - pub) <= band, "detail": ""})
    table = pd.DataFrame(rows).set_index("comparison")
    return table, bool(table["holds"].all())


def e6_line(table: pd.DataFrame, met: bool) -> str:
    """The verdict of E6 in words, with every comparison that does not hold named with its arithmetic."""
    n, n_all = int(table["holds"].sum()), len(table)
    text = f"E6: {'MET' if met else 'NOT MET'}. {n} of {n_all} comparisons hold."
    first = table.iloc[0]
    text += f" The market's alpha net of 10 basis points: {first['computed']:.2f} per cent a year, {first['detail']}."
    misses = table[~table["holds"]]
    if len(misses):
        text += " Outside: " + "; ".join(f"{i} {r['computed']:.2f} against {r['published']:.2f} ({r['level']})"
                                          for i, r in misses.iterrows()) + "."
    return text


def _category(significant: bool, value: float) -> str:
    return ("significantly positive" if value > 0 else "significantly negative") if significant else "not significant"


def e4(size_rate: float, factors: pd.DataFrame) -> tuple[pd.DataFrame, dict, bool]:
    """E4. `size_rate` is the size check's rejection rate. `factors` has one row per factor on Moreira and
    Muir's sample with the alpha, its Newey-West t-statistic (t_nw), the Sharpe ratio difference managed
    minus original (difference) and whether its bootstrap interval excludes zero (excludes_zero).

    The second part is read strictly, as the design ruled on 12 November 2026: a factor counts when
    the sign of its Sharpe ratio difference equals the sign of its alpha, and the bootstrap's verdict at 5
    per cent equals the Newey-West t-statistic's (|t| above 1.96 or not). The count by category, each test
    placing the factor as significantly positive, significantly negative or not significant, is returned
    beside it in no verdict. E4 is met when both parts hold."""
    rows = []
    for f, r in factors.iterrows():
        t_sig = abs(r["t_nw"]) > Z_5
        b_sig = bool(r["excludes_zero"])
        rows.append({
            "factor": f, "alpha": r["alpha"], "t (Newey-West)": r["t_nw"], "t significant": t_sig,
            "Sharpe difference": r["difference"], "bootstrap significant": b_sig,
            "signs equal": (r["alpha"] > 0) == (r["difference"] > 0),
            "significance equal": t_sig == b_sig,
            "category (t)": _category(t_sig, r["alpha"]), "category (bootstrap)": _category(b_sig, r["difference"]),
        })
    table = pd.DataFrame(rows).set_index("factor")
    table["counts (strict)"] = table["signs equal"] & table["significance equal"]
    table["same category"] = table["category (t)"] == table["category (bootstrap)"]
    lo, hi = C.E4_SIZE_RANGE
    parts = {
        "size": lo <= size_rate <= hi,
        "agreement": int(table["counts (strict)"].sum()) >= C.E4_MIN_FACTORS,
        "count strict": int(table["counts (strict)"].sum()),
        "count by category": int(table["same category"].sum()),
        "size rate": size_rate,
    }
    return table, parts, parts["size"] and parts["agreement"]


def e4_line(parts: dict, met: bool) -> str:
    """The verdict of E4 in words."""
    lo, hi = C.E4_SIZE_RANGE
    return (f"E4: {'MET' if met else 'NOT MET'}. Size check: {parts['size rate']:.1%} of the simulated null pairs rejected, "
            f"{'inside' if parts['size'] else 'outside'} {lo:.1%} to {hi:.1%}. Agreement of the bootstrap with the "
            f"Newey-West t-statistic in sign and in significance: {parts['count strict']} of 6, at least "
            f"{C.E4_MIN_FACTORS} required. In no verdict, agreement by category: {parts['count by category']} of 6.")
