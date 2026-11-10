"""
Checks src/sq/published.py against the journal PDFs, digit by digit.

The PDFs are copyrighted and live outside the repository (../papers/, under
the file names below). When a PDF or pdftotext is absent, its comparison is
skipped and only the internal consistency checks run. When both are present,
every transcribed number is re-read from the PDF's page with pdftotext and
compared exactly.
"""
from __future__ import annotations

import math
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import published as P  # noqa: E402

PAPERS = ROOT.parent / "papers"
PDF_NAMES = {
    "MM": "Moreira & Muir (2017) Volatility-Managed Portfolios.pdf",
    "COWY": "Cederburg et al (2020) On the performance of volatility-managed portfolios.pdf",
    "BSC": "Barroso & Santa-Clara (2015) Momentum has its moments.pdf",
}
# The PDF page of each journal page used below: MM's journal page is the PDF
# page plus 1610, COWY's plus 94, BSC's plus 110.
PAGE = {
    ("MM", 1612): 2, ("MM", 1619): 9, ("MM", 1620): 10, ("MM", 1625): 15, ("MM", 1626): 16,
    ("COWY", 99): 5, ("COWY", 104): 10, ("COWY", 106): 12,
    ("BSC", 112): 2, ("BSC", 113): 3, ("BSC", 116): 6,
}
DECIMAL = re.compile(r"-?\d+\.\d+")


def _pdf(key: str) -> pathlib.Path | None:
    p = PAPERS / PDF_NAMES[key]
    return p if p.exists() else None


def _page(key: str, journal_page: int, layout: bool = True) -> str:
    """One page's text: in layout mode for a table, in reading order for running text."""
    pdf = _pdf(key)
    mode = ["-layout"] if layout else []
    out = subprocess.run(["pdftotext", *mode, "-f", str(PAGE[key, journal_page]), "-l", str(PAGE[key, journal_page]),
                          str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    # MM and COWY print the minus as U+2212; BSC's font maps it to a control character followed by a space.
    return out.replace("−", "-").replace("\x01 ", "-").replace("\x01", "-")


def _numbers(s: str) -> list[float]:
    return [float(x) for x in DECIMAL.findall(s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").replace("%", " "))]


def _row(text: str, label: str, n: int, after: str | None = None, lookahead: int = 3) -> list[float]:
    """The first n decimal numbers of the first row whose line holds the label (a regular expression),
    searched after the marker when one is given; the numbers may sit up to `lookahead` lines below the label."""
    if after is not None:
        assert after in text, f"marker {after!r} not on the page"
        text = text.split(after, 1)[1]
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.search(label, line)
        if not m:
            continue
        for j in range(i, min(i + lookahead + 1, len(lines))):
            nums = _numbers(line[m.end():] if j == i else lines[j])
            if len(nums) >= n:
                return nums[:n]
    raise AssertionError(f"no row {label!r} with {n} numbers")


def _next_row(text: str, label: str, n: int, after: str | None = None) -> list[float]:
    """The n numbers on the first line below the labelled row that holds at least n numbers
    (the standard errors, t-statistics or p-values a table prints under its estimates)."""
    if after is not None:
        text = text.split(after, 1)[1]
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(label, line):
            for j in range(i + 1, min(i + 4, len(lines))):
                nums = _numbers(lines[j])
                if len(nums) >= n:
                    return nums[:n]
    raise AssertionError(f"no row under {label!r} with {n} numbers")


needs = {k: pytest.mark.skipif(_pdf(k) is None or shutil.which("pdftotext") is None,
                               reason=f"the {k} PDF or pdftotext is not available") for k in PDF_NAMES}


def test_internal_consistency():
    assert set(P.MM_TABLE_I) == set(P.FACTORS)
    assert all(len(v) == len(P.MM_TABLE_I_FIELDS) for v in P.MM_TABLE_I.values())
    for f in P.FACTORS:
        o, m = P.COWY_TABLE_1_ORIGINAL[f], P.COWY_TABLE_1_MANAGED[f]
        assert o[1] == m[1], f            # c* gives both the same standard deviation
        assert abs((m[2] - o[2]) - P.COWY_TABLE_1_DIFFERENCE[f][0]) <= 0.011, f
        s1, s2, d12, s3, d13 = P.COWY_TABLE_5[f]
        assert abs((s1 - s2) - d12) <= 0.011 and abs((s1 - s3) - d13) <= 0.011, f
    assert abs(P.mm_appraisal_from_table_i("Mkt-RF") - 0.33) < 0.005
    assert P.table("mm_table_i").shape == (6, 8)
    assert P.table("cowy_table_5").shape == (6, 7)


@needs["MM"]
def test_mm_table_i():
    t = _page("MM", 1619)
    a = "Panel A: Univariate Regressions"
    alpha = _row(t, r"Alpha \(α\)", 6, after=a)
    alpha_se = _next_row(t, r"Alpha \(α\)", 6, after=a)
    r2 = _row(t, r"^\s*R2\s", 6, after=a)
    rmse = _row(t, r"^\s*RMSE\s", 6, after=a)
    n_line = next(line for line in t.split(a, 1)[1].splitlines() if re.match(r"^\s*N\s", line))
    n = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", n_line)][:6]
    labels = {"Mkt-RF": "MktRF", "SMB": "SMB", "HML": "HML", "Mom": "Mom", "RMW": "RMW", "CMA": "CMA"}
    for k, f in enumerate(P.FACTORS):
        beta = _row(t, rf"^\s*{labels[f]}\s", 1, after=a)[0]
        beta_se = _next_row(t, rf"^\s*{labels[f]}\s", 1, after=a)[0]
        assert P.MM_TABLE_I[f] == (beta, beta_se, alpha[k], alpha_se[k], n[k], r2[k], rmse[k]), f


@needs["MM"]
def test_mm_text_appraisal_ratios():
    t1620 = " ".join(_page("MM", 1620, layout=False).split())
    assert re.search(r"ized appraisal ratio is 0\.34", t1620)
    for name, f in (("HML", "HML"), ("profitability", "RMW")):
        assert re.search(rf"{name} \({P.MM_TEXT_APPRAISAL_P1620[f]:.2f}\)", t1620), name
    t1612 = " ".join(_page("MM", 1612, layout=False).split())
    assert re.search(r"an appraisal ratio of 0\.33", t1612)


@needs["MM"]
def test_mm_tables_iv_and_v():
    t4 = _page("MM", 1625)
    row = _row(t4, r"Realized variance", 6, after="Transaction Costs of Volatility Timing")
    line = next(x for x in t4.split("Transaction Costs of Volatility Timing", 1)[1].splitlines()
                if "Realized variance" in x and "bps" in x)
    v = P.MM_TABLE_IV_MARKET
    assert row == [v["mean_abs_change_in_weight"], v["expected_return"], v["alpha"], v["alpha_1bp"], v["alpha_10bp"], v["alpha_14bp"]]
    assert int(re.search(r"(\d+)\s*bps", line).group(1)) == v["break_even_bp"]
    t5 = _page("MM", 1626)
    a = "Panel A: Weights and Performance"
    row = _row(t5, r"Realized variance", 7, after=a)
    se = _next_row(t5, r"Realized variance", 1, after=a)
    v = P.MM_TABLE_V_MARKET
    assert row == [v["alpha"], v["sharpe"], v["appraisal"], v["P50"], v["P75"], v["P90"], v["P99"]]
    assert se == [v["alpha_se"]]


@needs["COWY"]
def test_cowy_table_1():
    t = _page("COWY", 99)
    pa, pb = "Panel A: Performance measures for original", "Panel B: Performance measures for volatility-managed"
    for panel, marker in ((P.COWY_TABLE_1_ORIGINAL, pa), (P.COWY_TABLE_1_MANAGED, pb)):
        mean = _row(t, r"^\s*Mean\s", 6, after=marker)
        sd = _row(t, r"^\s*Standard deviation\s", 6, after=marker)
        sr = _row(t, r"^\s*Sharpe ratio\s", 6, after=marker)
        for k, f in enumerate(P.FACTORS):
            assert panel[f] == (mean[k], sd[k], sr[k]), (marker, f)
    d = _row(t, r"Sharpe ratio difference", 6)
    p = _next_row(t, r"Sharpe ratio difference", 6)
    corr = _row(t, r"Correlation with original factor", 6)
    q = {lab: _row(t, rf"^\s*{lab}\s", 6) for lab in ("P01", "P50", "P99")}
    for k, f in enumerate(P.FACTORS):
        assert P.COWY_TABLE_1_DIFFERENCE[f] == (d[k], p[k]), f
        assert P.COWY_TABLE_1_PANEL_D[f] == (corr[k], q["P01"][k], q["P50"][k], q["P99"][k]), f


@needs["COWY"]
def test_cowy_table_3():
    t = _page("COWY", 104)
    a = "Panel A.1"
    alpha = _row(t, r"Alpha, α \(%\)", 6, after=a)
    alpha_t = _next_row(t, r"Alpha, α \(%\)", 6, after=a)
    beta = _row(t, r"Beta, β", 6, after=a)
    beta_t = _next_row(t, r"Beta, β", 6, after=a)
    r2 = _row(t, r"^\s*R2\s", 6, after=a)
    ar = _row(t, r"Appraisal ratio, AR", 6, after=a)
    c = _row(t, r"Scaling parameter, c", 6, after=a)
    for k, f in enumerate(P.FACTORS):
        assert P.COWY_TABLE_3[f] == (alpha[k], alpha_t[k], beta[k], beta_t[k], r2[k], ar[k], c[k]), f


@needs["COWY"]
def test_cowy_table_5():
    t = _page("COWY", 106)
    a = "Panel A: Real-time combination strategies"
    s1 = _row(t, r"\[S1\] Combination strategy \(real time\)", 6, after=a)
    s2 = _row(t, r"\[S2\] Original factor \(real time\)", 6, after=a)
    d12 = _row(t, r"Difference, \[S1\].\[S2\]", 6, after=a)
    p12 = _next_row(t, r"Difference, \[S1\].\[S2\]", 6, after=a)
    s3 = _row(t, r"\[S3\] Combination strategy \(ex post optimal\)", 6, after=a)
    d13 = _row(t, r"Difference, \[S1\].\[S3\]", 6, after=a)
    p13 = _next_row(t, r"Difference, \[S1\].\[S3\]", 6, after=a)
    for k, f in enumerate(P.FACTORS):
        assert P.COWY_TABLE_5[f] == (s1[k], s2[k], d12[k], s3[k], d13[k]), f
        assert P.COWY_TABLE_5_P[f] == (p12[k], p13[k]), f


@needs["BSC"]
def test_bsc_tables_and_drawdowns():
    t1 = _page("BSC", 113)
    assert tuple(_row(t1, r"^\s*WML\s", 7)) == P.BSC_TABLE_1_WML
    t3 = _page("BSC", 116)
    assert tuple(_row(t3, r"^\s*WML\s", 7)) == P.BSC_TABLE_3_WML
    scaled = _row(t3, r"^\s*WMLn\s", 8)
    assert tuple(scaled[:7]) == P.BSC_TABLE_3_WML_SCALED and scaled[7] == P.BSC_TABLE_3_INFORMATION_RATIO
    t112 = " ".join(_page("BSC", 112, layout=False).split()).replace("- ", "-")
    m = re.search(r"maximum drawdown of raw momentum is (-\d+\.\d+)% versus (-\d+\.\d+)%", t112)
    assert m and (float(m.group(1)), float(m.group(2))) == (P.BSC_MAX_DRAWDOWN["WML"], P.BSC_MAX_DRAWDOWN["WML scaled"])
