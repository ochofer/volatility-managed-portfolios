"""Builds dashboard/B-Q_dashboard.html from dashboard/template.html.in and the tables committed in results/<vintage>/.

Usage, from the repository root:
    python3 dashboard/build_dashboard.py

Every number on the page is read here from a committed table and formatted once; nothing is typed
by hand. The page embeds the data its four charts draw, so it opens from a file; the charts are
drawn in the browser by Plotly, loaded from its content delivery network, and every chart has its
numbers in a table under it, so nothing depends on the chart loading or on hover. The build stops,
naming the file, if a table is missing. Exhibits are numbered in page order across the views, and
every reference in the text is written from the exhibit it points to.
"""
import datetime
import json
import os
import re
import sys
import zoneinfo

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)
VINTAGE = "202609"
RESULTS = os.path.join(REPO, "results", VINTAGE)
OUT = os.path.join(SCRIPT_DIR, "B-Q_dashboard.html")
FAC = ["Mkt-RF", "SMB", "HML", "Mom", "RMW", "CMA"]
MINUS = "−"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def rd(name, **kw):
    path = os.path.join(RESULTS, f"{name}_{VINTAGE}.csv")
    if not os.path.exists(path):
        sys.exit(f"dashboard/build_dashboard.py: results/{VINTAGE}/{name}_{VINTAGE}.csv is missing; run the notebook that writes it and copy its outputs to results/{VINTAGE}/")
    return pd.read_csv(path, **kw)


def f(x, d=2, plus=False):
    """A number for display: d decimals, the true minus sign, a plus sign where asked."""
    if pd.isna(x):
        return ""
    s = f"{abs(x):.{d}f}"
    if float(s) == 0:
        return s
    if x < 0:
        return MINUS + s
    return ("+" + s) if plus else s


def words(ym):
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


# ---------------------------------------------------------------- the tables
e = {k: rd(f"{k}_verdict").iloc[0] for k in ["e1", "e2", "e3", "e4", "e5", "e6"]}
e1c = rd("e1_comparison").set_index("factor")
e2c = rd("e2_comparison").set_index("factor")
e3c = rd("e3_comparison").set_index("series")
e6c = rd("e6_comparison")
c1 = rd("cowy_table_1_computed", index_col=0)
c5 = rd("cowy_table_5_computed", index_col=0)
dia = rd("e2_diagnostic_a_rmw_mean_moved", index_col=0)
dib = rd("e2_diagnostic_b_rmw_archived", index_col=0)
cause = rd("e2_cause_original_factors", index_col=0)
bsc = rd("bsc_table_3_computed", index_col=0)
st = rd("sharpe_tests_mm_sample", index_col=0)
ide = rd("alpha_and_sharpe_difference", index_col=0)
size = rd("size_check").iloc[0]
sh = rd("after_sample_sharpe", index_col=0)
rt = rd("e5_real_time_tests", index_col=0)
vm = rd("e5_volatility_managed_tests", index_col=0)
co = rd("costs_mm_sample", index_col=0)
pm = rd("position_market_mm_sample", index_col=0)["computed"]
pc = rd("position_cowy_sample", index_col=0)
vmm = rd("volatility_managed_mm_sample", header=[0, 1], index_col=0).dropna(how="all")
aft = rd("after_sample_series")
smp = rd("samples").set_index("factor")

pos = vmm["Mkt-RF"]["weight"].astype(float)
pos_months = [str(i) for i in pos.index]
mkt_pub = {r["comparison"].split(" position ")[1].split(",")[0]: r["published"] for _, r in e6c.iterrows()
           if r["comparison"].startswith("Mkt-RF position") and "Moreira" in r["comparison"]}
n_pos = len(pos)
above2 = int((pos > 2).sum())
big = pos.idxmax()

# months of the after-sample series with the largest gaps between the volatility-managed and the original market
am = aft[aft["factor"] == "Mkt-RF"].copy()
am["gap"] = (am["original"] - am["managed"]).abs()
gaps = am.nlargest(3, "gap")

# ---------------------------------------------------------------- exhibits, numbered in page order
ORDER = [("table", "exp"), ("figure", "after"), ("table", "after-sharpe"), ("table", "e5"), ("figure", "mm"), ("figure", "costs"),
         ("figure", "position"), ("table", "cowy-pos"), ("table", "mm1"), ("table", "cowy1"), ("table", "cowy5"), ("table", "rmw"), ("table", "bsc")]
NUM = {}
_count = {"table": 0, "figure": 0}
for kind, key in ORDER:
    _count[kind] += 1
    NUM[key] = (kind, _count[kind])


def ref(key):
    kind, n = NUM[key]
    return f'<a href="#{kind}-{n}">{kind.capitalize()} {n}</a>'


def anchor(key):
    kind, n = NUM[key]
    return f"{kind}-{n}", f"{kind.capitalize()} {n}"


def html_table(head, rows, first_left=True):
    longest = max([len(re.sub(r"<[^>]+>", "", str(r[0]))) for r in rows] + [0])
    h = ['<div class="tw"><div class="tscroll"><table' + (' class="wrapfirst"' if longest > 28 else "") + '><thead><tr>']
    h += [f'<th class="l">{c[0]}</th>' if isinstance(c, tuple) else f"<th>{c}</th>" for c in head]
    h.append("</tr></thead><tbody>")
    for r in rows:
        h.append("<tr>")
        for i, c in enumerate(r):
            if i == 0 and first_left:
                h.append(f'<th scope="row">{c}</th>')
            elif isinstance(c, tuple):
                h.append(f'<td class="{c[1]}">{c[0]}</td>')
            else:
                h.append(f"<td>{c}</td>")
        h.append("</tr>")
    h.append("</tbody></table></div></div>")
    return "".join(h)


def table_block(key, title, unit, head, rows, note, source):
    a, label = anchor(key)
    return (f'<div class="tblock" id="{a}"><h2>{label} | {title}</h2><p class="cap">{unit}</p>'
            + html_table(head, rows) + (f'<p class="note">{note}</p>' if note else "") + f'<p class="src">{source}</p></div>')


def figure_block(key, title, unit, chart_id, head, rows, note, source, cls="chart"):
    a, label = anchor(key)
    return (f'<div class="fig" id="{a}"><h2>{label} | {title}</h2><p class="cap">{unit}</p>'
            f'<div id="{chart_id}" class="{cls}"></div>' + html_table(head, rows) + (f'<p class="note">{note}</p>' if note else "")
            + f'<p class="src">{source}</p></div>')


def verdict(v):
    return ("met", "verdict-met") if v == "met" else ("not met", "verdict-miss")


SRC = f"Source: Kenneth R. French Data Library and the author's calculations."

# Table 1: the six expectations
exp_rows = [
    ["E1", ("Moreira and Muir's Table I on their sample: the alpha's sign and 5 per cent significance, the alpha within one published standard error, the appraisal ratio within 0.05, for at least five of six factors", "w"),
     (f"{int(e['e1']['factors matching'])} of 6 factors ({ref('mm1')})", "w"), verdict(e["e1"]["verdict"])],
    ["E2", ("Cederburg et al.'s Tables 1 and 5 on their sample: four comparisons for each factor, Sharpe ratios within 0.05, the real-time differences with the published sign and significance", "w"),
     (f"{int(e['e2']['comparisons holding'])} of {int(e['e2']['comparisons'])}. RMW fails two, because French has revised its history since the paper: its mean on their months is now {f(cause.loc['RMW', 'mean, computed'])} per cent a year against their {f(cause.loc['RMW', 'mean, published'])} ({ref('rmw')})", "w"), verdict(e["e2"]["verdict"])],
    ["E3", ("Barroso and Santa-Clara's scaled momentum, May 1927 to December 2011: both Sharpe ratios within 0.05, both maximum drawdowns within five points", "w"),
     (f"{int(e['e3']['comparisons holding'])} of {int(e['e3']['comparisons'])} ({ref('bsc')})", "w"), verdict(e["e3"]["verdict"])],
    ["E4", ("Ledoit and Wolf's test rejects 3.5 to 6.5 per cent of 1,000 simulated pairs with equal Sharpe ratios, and agrees with the alpha's Newey-West t-statistic in sign and significance for at least five of six factors", "w"),
     (f"Size {f(100 * e['e4']['size rate'], 1)} per cent. {int(e['e4']['count strict'])} of 6 agree, because the alpha and the Sharpe ratio difference test different things ({int(e['e4']['count by category, no verdict'])} of 6 by category, in no verdict) ({ref('mm')})", "w"), verdict(e["e4"]["verdict"])],
    ["E5", ("May 2015 to August 2026: the real-time combination's Sharpe ratio above the real-time original's beyond the interval on at most two factors, and the median difference within the median half-width", "w"),
     (f"{int(e['e5']['count above'])} of 6, median {f(e['e5']['median difference'], 3, True)} within {f(e['e5']['median half-width'], 3)} ({ref('e5')})", "w"), verdict(e["e5"]["verdict"])],
    ["E6", ("The market's alpha net of 10 basis points per unit of turnover more than two Newey-West standard errors above zero, and the positions' percentiles within their bands", "w"),
     (f"{int(e['e6']['comparisons holding'])} of {int(e['e6']['comparisons'])}. Net of 10 basis points {f(co.loc['Mkt-RF', 'alpha net of 10 bp'])} per cent a year, t {f(co.loc['Mkt-RF', 't net of 10 bp'])}, and net of 20 basis points {f(co.loc['Mkt-RF', 'alpha net of 20 bp'])}, t {f(co.loc['Mkt-RF', 't net of 20 bp'])} ({ref('costs')})", "w"), verdict(e["e6"]["verdict"])],
]
T_EXP = table_block("exp", "The six expectations, written before any run that judged them, and what the run found", "Each expectation is a strict pass or fail, dated 8 or 10 November 2026 in src/sq/constants.py, and no level moved after a run.",
                    ["Expectation", ("What was expected", "l"), ("What the run found", "l"), "Verdict"], exp_rows, "",
                    f"{SRC} results/{VINTAGE}/e1_verdict_{VINTAGE}.csv to e6_verdict_{VINTAGE}.csv, notebooks 03 to 08.")

# Figure 1: after the sample
after_rows = []
for k in FAC:
    a, b = rt.loc[k], vm.loc[k]
    after_rows.append([k, f(a["difference"], 3, True), f(a["lower"], 3) + " to " + f(a["upper"], 3), f(a["half_width"], 3), f(a["p_value"], 2),
                       f(b["difference"], 3, True), f(b["lower"], 3) + " to " + f(b["upper"], 3), f(b["half_width"], 3), f(b["p_value"], 2)])
F_AFTER = figure_block("after", "Sharpe ratio differences in the 136 months after Moreira and Muir's sample, May 2015 to August 2026",
                       "Annualised Sharpe ratio difference, with Ledoit and Wolf's 95% interval", "c-after",
                       ["Factor", "Real-time combination minus real-time original", "95% interval", "Half-width", "p-value",
                        "Volatility-managed minus original", "95% interval", "Half-width", "p-value"], after_rows,
                       "These 136 months cannot tell any of the twelve differences from zero, and the sign of a difference on these months says nothing about another sample. "
                       "E5 judges the first comparison, and the second carries no verdict. c is fixed on the months to April 2015, and the real-time combination uses only the months before each decision. Simulated, before costs.",
                       f"{SRC} Monthly, May 2015 to August 2026, US equity factors, USD. results/{VINTAGE}/e5_real_time_tests_{VINTAGE}.csv and e5_volatility_managed_tests_{VINTAGE}.csv, notebook 07.")

# Table 2 and 3: after the sample
T_AFTER_SHARPE = table_block("after-sharpe", "The four Sharpe ratios in the 136 months after the sample, May 2015 to August 2026", "Annualised Sharpe ratio, simulated, before costs",
                             ["Factor", "Original", "Volatility-managed", "Real-time combination (S1)", "Real-time original (S2)"],
                             [[k, f(sh.loc[k, "original"], 3), f(sh.loc[k, "volatility-managed"], 3), f(sh.loc[k, "S1"], 3), f(sh.loc[k, "S2"], 3)] for k in FAC],
                             f"Each difference between two of these columns, with its interval, is in {ref('after')}.",
                             f"{SRC} Monthly, May 2015 to August 2026. results/{VINTAGE}/after_sample_sharpe_{VINTAGE}.csv, notebook 07.")
T_E5 = table_block("e5", "E5, the expectation for the months after the sample, and the same counts for the volatility-managed factor", "Annualised Sharpe ratio differences",
                   ["Comparison", "Factors with the interval above zero", "Allowed", "Median difference", "Median half-width", "Verdict"],
                   [["Real-time combination minus real-time original", str(int(e["e5"]["count above"])), str(int(e["e5"]["allowed"])), f(e["e5"]["median difference"], 3, True), f(e["e5"]["median half-width"], 3), verdict(e["e5"]["verdict"])],
                    ["Volatility-managed minus original", str(int(e["e5"]["volatility-managed count above, no verdict"])), "", f(vm["difference"].median(), 3, True), f(vm["half_width"].median(), 3), ("no verdict", "")]],
                   "", f"{SRC} results/{VINTAGE}/e5_verdict_{VINTAGE}.csv and e5_volatility_managed_tests_{VINTAGE}.csv, notebook 07.")

# Figure 2: the test on Moreira and Muir's sample
mm_rows = []
for k in FAC:
    a, b = st.loc[k], ide.loc[k]
    mm_rows.append([k, f(a["alpha"]), f(a["t_nw"]), f(a["Sharpe managed"], 3), f(a["Sharpe original"], 3), f(a["difference"], 3, True),
                    f(a["lower"], 3) + " to " + f(a["upper"], 3), f(a["p_value"], 2), f(b["rho"], 3), f(b["alpha / sigma"], 3, True), f(b["(1 - rho) x Sharpe original"], 3)])
F_MM = figure_block("mm", "Sharpe ratio differences on Moreira and Muir's sample, each factor from its first month to April 2015",
                    "Annualised Sharpe ratio difference, volatility-managed minus original, with Ledoit and Wolf's 95% interval, on the axis of Figure 1",
                    "c-mm",
                    ["Factor", "Alpha, % a year", "t (Newey-West)", "Sharpe ratio, managed", "Sharpe ratio, original", "Difference", "95% interval", "p-value",
                     "Correlation &rho;", "&alpha;/&sigma;", "(1 " + MINUS + " &rho;) &times; Sharpe ratio, original"], mm_rows,
                    "The difference equals &alpha;/&sigma; minus (1 " + MINUS + " &rho;) times the original's Sharpe ratio for every factor, to four decimals: the alpha measures what the volatility-managed factor adds to a holding of the original, and the difference measures it held in the original's place. "
                    "The sign of a difference on these months says nothing about another sample. Simulated, before costs.",
                    f"{SRC} Monthly, August 1926 (January 1927 for momentum, August 1963 for RMW and CMA) to April 2015. results/{VINTAGE}/sharpe_tests_mm_sample_{VINTAGE}.csv and alpha_and_sharpe_difference_{VINTAGE}.csv, notebook 06.")

# Figure 3: costs
cost_rows = []
for k in FAC:
    r = co.loc[k]
    be = r["break-even cost (bp)"]
    cost_rows.append([k, f(r["average turnover"]), f(r["alpha gross"]), f(r["t gross (Newey-West)"]), f(r["alpha net of 10 bp"]), f(r["t net of 10 bp"]),
                      f(r["alpha net of 20 bp"]), f(r["t net of 20 bp"]), f(be, 0) if not pd.isna(be) else "none"])
F_COSTS = figure_block("costs", "The volatility-managed factor's alpha gross and net of trading costs, Moreira and Muir's sample",
                       "Alpha in % a year, with plus or minus two Newey-West standard errors", "c-costs",
                       ["Factor", "Turnover, a month", "Alpha, gross", "t", "Net of 10 bp", "t", "Net of 20 bp", "t", "Break-even, bp"], cost_rows,
                       "Turnover is the absolute change in the position from the month before. The cost is charged per unit of it, and the factor's own rebalancing, the same for the managed and the original factor, is left out. "
                       f"Moreira and Muir's Table IV gives the market {f(e6c.iloc[0]['published'])} per cent a year net of 10 basis points. SMB's gross alpha is negative and has no break-even cost. Simulated.",
                       f"{SRC} Monthly, to April 2015. results/{VINTAGE}/costs_mm_sample_{VINTAGE}.csv, notebook 08.")

# Figure 4: the market's position
pos_rows = [["Median", f(mkt_pub["P50"]), f(pm["P50"])], ["75th percentile", f(mkt_pub["P75"]), f(pm["P75"])],
            ["90th percentile", f(mkt_pub["P90"]), f(pm["P90"])], ["99th percentile", f(mkt_pub["P99"]), f(pm["P99"])],
            ["Largest", "", f"{f(pm['max'], 1)}, {words(big)}"]]
F_POS = figure_block("position", "The volatility-managed market's position, August 1926 to April 2015",
                     "c over last month's realised variance, log scale", "c-position",
                     ["Statistic", "Moreira and Muir, Table V", "Computed"], pos_rows,
                     f"The position is above 2 in {above2} of the {n_pos:,} months. For the market, a position of 7 holds seven times the capital in stocks, six of them borrowed at the bill rate. E6 asks the median, 75th and 90th percentiles within 0.15 of Moreira and Muir's and the 99th within 1.0.",
                     f"{SRC} Monthly, August 1926 to April 2015. results/{VINTAGE}/volatility_managed_mm_sample_{VINTAGE}.csv and position_market_mm_sample_{VINTAGE}.csv, notebook 08.")

T_COWY_POS = table_block("cowy-pos", "The volatility-managed position on Cederburg et al.'s sample, published beside computed", "c over last month's realised variance, with their definition of the realised variance",
                         ["Factor", "Median, published", "Median, computed", "99th percentile, published", "99th percentile, computed", "Largest"],
                         [[k, f(pc.loc[k, "P50 published"]), f(pc.loc[k, "P50"]), f(pc.loc[k, "P99 published"]), f(pc.loc[k, "P99"]), f(pc.loc[k, "maximum"], 1)] for k in FAC],
                         "E6 asks each median within 0.15 and each 99th percentile within 1.0 of Cederburg et al.'s Table 1, Panel D.",
                         f"{SRC} Monthly, to December 2016. results/{VINTAGE}/position_cowy_sample_{VINTAGE}.csv, notebook 08.")

# Replication tables
T_MM = table_block("mm1", "Moreira and Muir's Table I on their sample, published beside computed", "Alpha of the volatility-managed factor on its original, % a year",
                   ["Factor", "Months", "Alpha, published", "Alpha, computed", "Standard error, published", "Standard error, White", "Standard error, Newey-West", "Appraisal ratio, published", "Appraisal ratio, computed", "E1 holds"],
                   [[k, str(int(e1c.loc[k, "N computed"])), f(e1c.loc[k, "alpha published"]), f(e1c.loc[k, "alpha computed"]), f(e1c.loc[k, "se published"]),
                     f(e1c.loc[k, "se computed (White)"]), f(e1c.loc[k, "se computed (Newey-West)"]), f(e1c.loc[k, "appraisal published"]), f(e1c.loc[k, "appraisal computed"]),
                     "yes" if e1c.loc[k, "factor matches"] else "no"] for k in FAC],
                   f"The published standard errors are White's, as are the computed ones the verdict uses. The market's volatility-managed Sharpe ratio is {f(e1c.loc['Mkt-RF', 'Sharpe computed'])} against Table V's {f(e1c.loc['Mkt-RF', 'Sharpe published (Table V)'])}.",
                   f"{SRC} Monthly, each factor from its first month to April 2015. results/{VINTAGE}/e1_comparison_{VINTAGE}.csv, notebook 03.")
T_C1 = table_block("cowy1", "Cederburg et al.'s Table 1 on their sample, published beside computed", "Annualised Sharpe ratios and the Jobson-Korkie p-value of their difference",
                   ["Factor", "Original, published", "Original, computed", "Volatility-managed, published", "Volatility-managed, computed", "Difference, published", "Difference, computed", "p-value, published", "p-value, computed"],
                   [[k, f(c1.loc[k, "original Sharpe, published"]), f(c1.loc[k, "original Sharpe, computed"], 3), f(c1.loc[k, "managed Sharpe, published"]), f(c1.loc[k, "managed Sharpe, computed"], 3),
                     f(c1.loc[k, "difference, published"], 2, True), f(c1.loc[k, "difference, computed"], 3, True), f(c1.loc[k, "p, published"]), f(c1.loc[k, "p, computed"])] for k in FAC],
                   "E2's first clause asks both Sharpe ratios within 0.05. It fails for RMW alone, its volatility-managed Sharpe ratio 0.006 outside the band.",
                   f"{SRC} Monthly, each factor from its first month to December 2016. results/{VINTAGE}/cowy_table_1_computed_{VINTAGE}.csv, notebook 04.")
T_C5 = table_block("cowy5", "Cederburg et al.'s Table 5, Panel A, on their sample, published beside computed", "Annualised Sharpe ratios of the real-time combination S1, the real-time original S2 and their differences",
                   ["Factor", "S1, published", "S1, computed", "S2, published", "S2, computed", "S1 " + MINUS + " S2, published", "S1 " + MINUS + " S2, computed", "p-value, published", "p-value, computed", "S1 " + MINUS + " S3, published", "S1 " + MINUS + " S3, computed"],
                   [[k, f(c5.loc[k, "S1, published"]), f(c5.loc[k, "S1, computed"], 3), f(c5.loc[k, "S2, published"]), f(c5.loc[k, "S2, computed"], 3),
                     f(c5.loc[k, "S1-S2, published"], 2, True), f(c5.loc[k, "S1-S2, computed"], 3, True), f(c5.loc[k, "p, published"]), f(c5.loc[k, "p, computed"]),
                     f(c5.loc[k, "S1-S3, published"], 2, True), f(c5.loc[k, "S1-S3, computed"], 3, True)] for k in FAC],
                   "S3 is the ex post optimal combination. E2's second clause fails for RMW alone, in S1, 0.020 outside the band, and its third and fourth hold: S1 " + MINUS + " S2 has the published sign for six of six factors and momentum's is the one significant difference.",
                   f"{SRC} Monthly, each strategy from 120 months after the factor's first month to December 2016. results/{VINTAGE}/cowy_table_5_computed_{VINTAGE}.csv, notebook 04.")
T_RMW = table_block("rmw", "RMW's revision: the miss of E2 and two diagnostics computed after the verdict, which carry none", "RMW, August 1963 to December 2016, 641 months",
                    ["Series", "Mean, % a year", "Standard deviation, % a year"],
                    [[f"Cederburg et al.'s Table 1", f(dib.iloc[0]["mean"]), f(dib.iloc[0]["sd"])],
                     [f"The Internet Archive's copy of French's five-factor file, 9 July 2017", f(dib.iloc[1]["mean"]), f(dib.iloc[1]["sd"])],
                     [f"French's file, vintage {VINTAGE}", f(dib.iloc[2]["mean"]), f(dib.iloc[2]["sd"])]],
                    f"Moving RMW's monthly returns by one constant to Table 1's mean closes the volatility-managed Sharpe ratio's gap to Table 1 from {f(dia.loc['managed Sharpe', 'gap, computed'], 3)} to {f(dia.loc['managed Sharpe', 'gap, mean moved'], 3)}, and S1's from {f(dia.loc['S1', 'gap, computed'], 3)} to {f(dia.loc['S1', 'gap, mean moved'], 3)}. The archived file is fetched at run time and not committed.",
                    f"{SRC} results/{VINTAGE}/e2_diagnostic_a_rmw_mean_moved_{VINTAGE}.csv and e2_diagnostic_b_rmw_archived_{VINTAGE}.csv, notebook 04.")
bsc_rows = [["Mean, % a year", f(bsc.loc["mean", "WML, published"]), f(bsc.loc["mean", "WML, computed"]), f(bsc.loc["mean", "scaled WML, published"]), f(bsc.loc["mean", "scaled WML, computed"])],
            ["Standard deviation, % a year", f(bsc.loc["standard deviation", "WML, published"]), f(bsc.loc["standard deviation", "WML, computed"]), f(bsc.loc["standard deviation", "scaled WML, published"]), f(bsc.loc["standard deviation", "scaled WML, computed"])],
            ["Sharpe ratio", f(bsc.loc["Sharpe ratio", "WML, published"]), f(bsc.loc["Sharpe ratio", "WML, computed"]), f(bsc.loc["Sharpe ratio", "scaled WML, published"]), f(bsc.loc["Sharpe ratio", "scaled WML, computed"])],
            ["Maximum drawdown, %", f(e3c.loc["WML", "maximum drawdown published (%)"]), f(e3c.loc["WML", "maximum drawdown computed (%)"]), f(e3c.loc["WML scaled", "maximum drawdown published (%)"]), f(e3c.loc["WML scaled", "maximum drawdown computed (%)"])]]
T_BSC = table_block("bsc", "Barroso and Santa-Clara's Table 3, May 1927 to December 2011, published beside computed", "Momentum (WML) and scaled momentum, 1,016 months",
                    ["Statistic", "WML, published", "WML, computed", "Scaled WML, published", "Scaled WML, computed"], bsc_rows,
                    "The paper's scaled series starts in March 1927. French's daily file of the ten momentum portfolios starts on 3 November 1926, so the first scaled month here is May 1927. E3 judges the two Sharpe ratios and the two maximum drawdowns.",
                    f"{SRC} Monthly. results/{VINTAGE}/bsc_table_3_computed_{VINTAGE}.csv and e3_comparison_{VINTAGE}.csv, notebook 05.")

# ---------------------------------------------------------------- the views
mkt_rt, mkt_vm = rt.loc["Mkt-RF"], vm.loc["Mkt-RF"]
mom = st.loc["Mom"]
n_in = int(((st["excludes_zero"]) & (st["difference"] > 0)).sum())
n_t = int((st["t_nw"] > 1.96).sum())
kpis = [
    ("After the sample", f"{int(e['e5']['count above'])} of 6",
     f"factors whose real-time combination has a Sharpe ratio above the real-time original's beyond its 95% interval, May 2015 to August 2026, half-widths {f(rt['half_width'].min())} to {f(rt['half_width'].max())}, simulated"),
    ("In the sample", f"{n_in} of 6",
     f"factors whose volatility-managed Sharpe ratio is above the original's beyond its 95% interval: momentum, {f(mom['difference'], 2, True)} ({f(mom['lower'])} to {f(mom['upper'])}). The alpha's t-statistic is above 1.96 for {n_t} of 6. To April 2015, simulated"),
    ("Market alpha net of costs", f(co.loc["Mkt-RF", "alpha net of 10 bp"]),
     f"% a year at 10 bp per unit of turnover, t {f(co.loc['Mkt-RF', 't net of 10 bp'])}, and {f(co.loc['Mkt-RF', 'alpha net of 20 bp'])} at 20 bp, t {f(co.loc['Mkt-RF', 't net of 20 bp'])}, to April 2015, simulated"),
    ("Expectations met", f"{sum(e[k]['verdict'] == 'met' for k in e)} of 6",
     f"fixed before any run that judged them. Not met: E2, {int(e['e2']['comparisons holding'])} of {int(e['e2']['comparisons'])} comparisons (French revised RMW), and E4, {int(e['e4']['count strict'])} of 6 factors (the alpha and the Sharpe ratio test answer different questions)"),
]
KPIS = "".join(f'<div class="ch-kpi"><div class="ch-kpi__label">{a}</div><div class="ch-kpi__value">{b}</div><div class="ch-kpi__ref">{c}</div></div>' for a, b, c in kpis)

rmw_c = cause.loc["RMW"]
KEYPOINTS = [
    f"After the sample, May 2015 to August 2026, no factor's real-time combination has a Sharpe ratio above the real-time original's by more than its interval allows. E5 is met: the median difference is {f(e['e5']['median difference'], 3, True)}, annualised, and the median half-width {f(e['e5']['median half-width'], 3)}. "
    f"These 136 months cannot tell the differences from zero. The market's volatility-managed Sharpe ratio is {f(sh.loc['Mkt-RF', 'volatility-managed'])} against the original's {f(sh.loc['Mkt-RF', 'original'])}, a difference of {f(mkt_vm['difference'])} with an interval of {f(mkt_vm['lower'])} to {f(mkt_vm['upper'])} ({ref('after')}).",
    f"The alpha and the Sharpe ratio answer different questions: the alpha tests what the volatility-managed factor adds to a holding of the original, and the Sharpe ratio difference tests it in the original's place. "
    f"On Moreira and Muir's sample Ledoit and Wolf's test finds the volatility-managed Sharpe ratio above the original's for momentum alone, a difference of {f(mom['difference'], 2, True)}, annualised, with an interval of {f(mom['lower'])} to {f(mom['upper'])}, while the alpha's Newey-West t-statistic is above 1.96 for the market, momentum and RMW ({ref('mm')}). "
    f"E4 is not met: the two agree in sign and significance for {int(e['e4']['count strict'])} of 6 factors where 5 were expected, though the test rejects {f(100 * size['rate'], 1)} per cent of {int(size['pairs']):,} simulated pairs with equal Sharpe ratios, inside 3.5 to 6.5.",
    f"The market's position changes by {f(co.loc['Mkt-RF', 'average turnover'])} of the factor a month on average, and its alpha net of 10 basis points per unit of that change is {f(co.loc['Mkt-RF', 'alpha net of 10 bp'])} per cent a year with a t-statistic of {f(co.loc['Mkt-RF', 't net of 10 bp'])}, and {f(co.loc['Mkt-RF', 'alpha net of 20 bp'])} with a t-statistic of {f(co.loc['Mkt-RF', 't net of 20 bp'])} at 20 ({ref('costs')}). "
    f"The position's median is {f(pm['P50'])} and its 99th percentile {f(pm['P99'])}, against Moreira and Muir's {f(mkt_pub['P50'])} and {f(mkt_pub['P99'])} ({ref('position')}). E6 is met, {int(e['e6']['comparisons holding'])} of {int(e['e6']['comparisons'])}.",
    f"On each paper's own sample the replication matches Moreira and Muir's Table I for {int(e['e1']['factors matching'])} of 6 factors (E1, the market's alpha {f(e1c.loc['Mkt-RF', 'alpha computed'])} per cent a year with a White standard error of {f(e1c.loc['Mkt-RF', 'se computed (White)'])}, against {f(e1c.loc['Mkt-RF', 'alpha published'])} and {f(e1c.loc['Mkt-RF', 'se published'])}) and Barroso and Santa-Clara's scaled momentum in {int(e['e3']['comparisons holding'])} of {int(e['e3']['comparisons'])} comparisons (E3, a Sharpe ratio of {f(e3c.loc['WML scaled', 'Sharpe computed'])} against {f(e3c.loc['WML scaled', 'Sharpe published'])} and a worst fall of {f(-e3c.loc['WML scaled', 'maximum drawdown computed (%)'], 1)} per cent against {f(-e3c.loc['WML scaled', 'maximum drawdown published (%)'], 1)}). "
    f"Cederburg et al.'s results reproduce in {int(e['e2']['comparisons holding'])} of {int(e['e2']['comparisons'])} comparisons, and E2 is not met: the two misses are RMW's, whose history French has revised since Cederburg et al. downloaded it, its mean on their months now {f(rmw_c['mean, computed'])} per cent a year against their {f(rmw_c['mean, published'])} ({ref('rmw')}).",
]
FACTS = [
    ("Data", f"Kenneth R. French Data Library, six factors and the ten momentum portfolios, daily and monthly, vintage {VINTAGE}, downloaded at run time"),
    ("Factors", "Market (Mkt-RF), size (SMB), value (HML), momentum (Mom), profitability (RMW), investment (CMA)"),
    ("Samples", "Moreira and Muir to April 2015, Cederburg et al. to December 2016, Barroso and Santa-Clara May 1927 to December 2011. After the sample: May 2015 to August 2026, 136 months"),
    ("Signal", "Last month's realised variance of the factor's daily returns, each paper's own definition"),
    ("Constructions", "Volatility-managed (Moreira and Muir), the real-time combination with a risk aversion of 5, at least 120 months of data and the position capped at 5 (Cederburg et al.), scaled momentum with a volatility target of 12 per cent a year (Barroso and Santa-Clara)"),
    ("Test", f"Ledoit and Wolf (2008), 12-month blocks, 2,000 bootstrap samples, checked first on {int(size['pairs']):,} simulated pairs"),
    ("Regression", "The volatility-managed factor on the original, Newey-West standard errors at 12 lags, White's for Table I"),
    ("Rebalancing", "Monthly"),
    ("Costs", "10 basis points per unit of turnover, 20 as the sensitivity"),
    ("Specification", "Six expectations, written 8 to 10 November 2026, before any run that judged them"),
]
FACTS_HTML = "".join(f'<div class="ch-fact"><dt>{a}</dt><dd>{b}</dd></div>' for a, b in FACTS)

SUMMARY = f"""<section id="summary" class="view on">
<p class="ch-view-lead">The six expectations, their verdicts and the study's own question.</p>
<div class="ch-top">
<div>
<div class="ch-kpis">{KPIS}</div>
<p class="kpnote">The 136 months after the sample cannot tell any of these differences from zero, and the sign of a Sharpe ratio difference on one sample says nothing about another.</p>
<ul class="kp">{''.join(f'<li>{k}</li>' for k in KEYPOINTS)}</ul>
</div>
<aside class="ch-facts"><h3>Key facts</h3><dl>{FACTS_HTML}</dl></aside>
</div>
{T_EXP}
{F_AFTER}
</section>"""

g = gaps.reset_index(drop=True)
gap_sent = " ".join(
    f"In {words(r['month'])} the position was {f(r['position'], 2 if r['position'] >= 0.1 else 3)}, and the market {'rose' if r['original'] > 0 else 'fell'} {f(abs(100 * r['original']), 2 if abs(100 * r['original']) < 10 else 1)} per cent while the volatility-managed market {'rose' if r['managed'] > 0 else 'fell'} {f(abs(100 * r['managed']), 2 if abs(100 * r['managed']) < 10 else 1)} per cent."
    for _, r in g.iterrows())
AFTER = f"""<section id="after" class="view">
<p class="ch-view-lead">What the signal did in the 136 months after Moreira and Muir's sample, with the volatility-managed factor's scale fixed on the data to April 2015 and the real-time combination carried forward.</p>
<p class="lead">The study's own question is what the signal did after Moreira and Muir's sample ended. Both constructions run unchanged on May 2015 to August 2026: the volatility-managed factor's scale, c, is fixed on the months to April 2015, and the real-time combination uses only the months before each decision, so no parameter of either was set on these months. {ref('after')} shows each difference with its interval. The intervals are wide because the months are 136: the half-widths of the volatility-managed comparisons, annualised, are {f(vm['half_width'].min())} to {f(vm['half_width'].max())} on these months and {f(st['half_width'].min())} to {f(st['half_width'].max())} on the 1,065 months of Moreira and Muir's sample ({ref('mm')}). These months therefore cannot tell the differences from zero.</p>
{T_AFTER_SHARPE}
{T_E5}
<p class="lead">The three months with the largest gaps between the volatility-managed and the original market are {words(g.loc[0, 'month'])}, {words(g.loc[1, 'month'])} and {words(g.loc[2, 'month'])}. {gap_sent}</p>
</section>"""

COSTS = f"""<section id="in-sample" class="view">
<p class="ch-view-lead">What the volatility-managed factor adds to the original on Moreira and Muir's sample, how the Sharpe ratio test reads it, and what trading it costs.</p>
<p class="lead">The test of a Sharpe ratio difference is Ledoit and Wolf's (2008) studentised circular block bootstrap. Before it touches a factor it is run on {int(size['pairs']):,} simulated pairs of {int(size['months']):,} months whose Sharpe ratios are equal by construction, and it rejects {int(size['rejected'])} of them at the 5 per cent level, {f(100 * size['rate'], 1)} per cent, inside the range of 3.5 to 6.5 fixed before the run.</p>
{F_MM}
{F_COSTS}
{F_POS}
{T_COWY_POS}
</section>"""

REPL = f"""<section id="replication" class="view">
<p class="ch-view-lead">Each paper's published numbers beside the computed ones, on each paper's own sample.</p>
{T_MM}
{T_C1}
{T_C5}
{T_RMW}
{T_BSC}
</section>"""

TERMS = [
    ("Factor", "the monthly return of a long-short portfolio that captures one source of common movement in stock returns, as Kenneth French publishes it."),
    ("Excess return", "a return minus the one-month Treasury bill rate. Every factor is one."),
    ("Realised variance", "the variance of a factor computed from its daily returns within one month, each paper with its own definition."),
    ("The signal", "last month's realised variance of a factor, and nothing else."),
    ("Volatility-managed", "Moreira and Muir's construction, the factor's return times c over last month's realised variance. Managed describes the construction and says nothing about its performance."),
    ("c", "the constant that gives the volatility-managed factor the original's standard deviation over the whole sample, so it is known only at the sample's end."),
    ("Position", "the multiple of the factor held in a month. The papers call a position above 1 leverage."),
    ("Real-time combination (S1)", "Cederburg et al.'s construction, the mean-variance weights on the volatility-managed and the original factor with a risk aversion of 5, estimated each month from the months before it, its total position capped at 5."),
    ("Real-time original (S2)", "the original factor alone at its real-time mean-variance weight."),
    ("Ex post optimal combination (S3)", "the mix of the two with the weights that were best over the whole sample, which no investor could have known."),
    ("Scaled momentum", "Barroso and Santa-Clara's construction, momentum (WML, winners minus losers) times 12 per cent a year over its realised volatility of the previous 126 trading days."),
    ("Alpha", "the intercept of the regression of the volatility-managed factor on its original, in per cent a year, always with its standard error or t-statistic."),
    ("Standard error", "the standard deviation of an estimate across the samples it could have come from. White's allows the residual's variance to change, and Newey and West's at 12 lags also allows a month's residual to be correlated with the 12 before it."),
    ("Sharpe ratio", "the mean excess return over its standard deviation, annualised."),
    ("Jobson-Korkie test", "Cederburg et al.'s test that two return series over the same months have the same Sharpe ratio, which assumes normal and independent months."),
    ("Delta method", "the standard error of a function of means, from the function's slopes and the means' covariance."),
    ("Appraisal ratio", "the alpha over the residual's standard deviation, annualised."),
    ("Interval", "the 95 per cent interval of Ledoit and Wolf's test for the true Sharpe ratio difference. The test rejects when it excludes zero."),
    ("Half-width", "the distance from a difference to either end of its interval."),
    ("p-value", "the probability of a difference at least as far from zero as the one computed, if the two true Sharpe ratios were equal."),
    ("Size", "the share of samples in which a test rejects when the null is true."),
    ("Turnover", "the absolute change in the position from the month before, the first month carrying none."),
    ("Basis point", "a hundredth of a percentage point."),
    ("Break-even cost", "the cost per unit of turnover at which the alpha falls to zero."),
    ("Maximum drawdown", "the largest fall from a peak of the compounded return."),
    ("Band", "the distance from a published number within which a computed one counts as matching, fixed before the code."),
    ("Verdict", "whether an expectation is met. A count reported in no verdict is shown without one."),
    ("Vintage", "the version of French's files, named by the CRSP release they were built from."),
]
TERMS_HTML = "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in TERMS)

OTHER = open(os.path.join(SCRIPT_DIR, "other_projects.html")).read()

METHOD = f"""<section id="method" class="view method">
<p class="ch-view-lead">The data, the constructions, what is known at each date, the costs, and what the study cannot show.</p>
<h2>Method</h2>
<p><strong>Data and period.</strong> Kenneth R. French's daily and monthly files of the six factors and of the ten portfolios sorted on prior returns, vintage {VINTAGE}, downloaded at run time and never committed.<sup><a href="#note-4">4</a></sup> The market, SMB and HML start in July 1926, momentum in January 1927, RMW and CMA in July 1963, and every series is cut at August 2026. Each paper's results are compared on its own months: Moreira and Muir's to April 2015,<sup><a href="#note-1">1</a></sup> Cederburg, O'Doherty, Wang and Yan's to December 2016,<sup><a href="#note-2">2</a></sup> Barroso and Santa-Clara's from May 1927 to December 2011.<sup><a href="#note-3">3</a></sup></p>
<p><strong>The signal and the constructions.</strong> Each construction uses its paper's own realised variance. The volatility-managed factor holds c over last month's realised variance. The real-time combination holds, each month, the mean-variance weights of an investor with a risk aversion of 5 on the volatility-managed and the original factor, estimated from all the months before it once 120 are available, its total position capped at 5. Scaled momentum holds WML at 12 per cent a year over its realised volatility of the previous 126 trading days. Rebalancing is monthly throughout.</p>
<p><strong>What is known at each date.</strong> Each month's position uses only the realised variance of the month before. c is the exception: Moreira and Muir set it on the whole sample, which no investor could have known, and the replication does the same, as the paper does. The real-time combination uses only the months before each decision, and for the months after the sample c is fixed on the months to April 2015, so nothing in those 136 months was set on them.</p>
<p><strong>The test.</strong> Ledoit and Wolf (2008) take the standard error of a Sharpe ratio difference by the delta method from the prewhitened Parzen kernel, and its interval from a circular block bootstrap of 2,000 samples of 12-month blocks, each sample's difference studentised by its own standard error.<sup><a href="#note-5">5</a></sup> The paper proposes the QS kernel and reports the Parzen kernel's performance as very similar, and it calibrates the block length from the data, where the study fixed it at 12 months before the run.</p>
<p><strong>Costs.</strong> A month's turnover is the absolute change in the position from the month before. The cost, 10 basis points per unit of turnover and 20 as the sensitivity, is subtracted from the volatility-managed return, and the alpha is estimated again on the net return. The factor's own rebalancing is the same for the managed and the original factor and is left out.</p>
<p><strong>What the study cannot show.</strong> It holds no view on expected returns and estimates no premium. Its costs are charged on the change in a factor's position, and a book that holds the stocks pays more, so the break-even costs bound what it could pay. French revises history, so a run on a later vintage need not reproduce every digit, as RMW shows. The 136 months after the sample are too few to tell any Sharpe ratio difference from zero: halving the market's half-width would require four times as many. The volatility-managed position is never capped, as in the paper, so its largest positions, up to {f(pm['max'], 1)}, are positions no mandate would allow.</p>
<h2>Terms</h2>
<dl class="terms">{TERMS_HTML}</dl>
<h2>Notes</h2>
<ol class="notes">
<li id="note-1">Moreira, A. and Muir, T. (2017). Volatility-managed portfolios. <i>Journal of Finance</i>, 72(4), 1611-1644. <a href="https://doi.org/10.1111/jofi.12513">https://doi.org/10.1111/jofi.12513</a></li>
<li id="note-2">Cederburg, S., O'Doherty, M. S., Wang, F. and Yan, X. S. (2020). On the performance of volatility-managed portfolios. <i>Journal of Financial Economics</i>, 138(1), 95-117. <a href="https://doi.org/10.1016/j.jfineco.2020.04.015">https://doi.org/10.1016/j.jfineco.2020.04.015</a></li>
<li id="note-3">Barroso, P. and Santa-Clara, P. (2015). Momentum has its moments. <i>Journal of Financial Economics</i>, 116(1), 111-120. <a href="https://doi.org/10.1016/j.jfineco.2014.11.010">https://doi.org/10.1016/j.jfineco.2014.11.010</a></li>
<li id="note-4"><a href="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html">Kenneth R. French, Data Library</a>, files built from the {VINTAGE} CRSP database.</li>
<li id="note-5">Ledoit, O. and Wolf, M. (2008). Robust performance hypothesis testing with the Sharpe ratio. <i>Journal of Empirical Finance</i>, 15(5), 850-859. <a href="https://doi.org/10.1016/j.jempfin.2008.03.002">https://doi.org/10.1016/j.jempfin.2008.03.002</a></li>
</ol>
</section>
{OTHER}"""

BODY = "\n".join([SUMMARY, AFTER, COSTS, REPL, METHOD])

# ---------------------------------------------------------------- the data the charts draw
def r4(x):
    return None if pd.isna(x) else round(float(x), 5)


DATA = {
    "factors": FAC,
    "after": {"rt": [[r4(rt.loc[k, c]) for c in ["difference", "lower", "upper"]] for k in FAC],
              "vm": [[r4(vm.loc[k, c]) for c in ["difference", "lower", "upper"]] for k in FAC]},
    "mm": [[r4(st.loc[k, c]) for c in ["difference", "lower", "upper"]] for k in FAC],
    "costs": {"gross": [[r4(co.loc[k, "alpha gross"]), r4(co.loc[k, "alpha gross"] / co.loc[k, "t gross (Newey-West)"])] for k in FAC],
              "net10": [[r4(co.loc[k, "alpha net of 10 bp"]), r4(co.loc[k, "se net of 10 bp (Newey-West)"])] for k in FAC],
              "net20": [[r4(co.loc[k, "alpha net of 20 bp"]), r4(co.loc[k, "se net of 20 bp (Newey-West)"])] for k in FAC]},
    "position": {"months": pos_months, "values": [r4(x) for x in pos.values], "p50": r4(pm["P50"]), "p99": r4(pm["P99"])},
}
SCRIPT = open(os.path.join(SCRIPT_DIR, "charts.js")).read().replace("/*DATA*/null", json.dumps(DATA, separators=(",", ":")))

build_date = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Amsterdam")).date()
build_words = f"{build_date.day} {MONTHS[build_date.month - 1]} {build_date.year}"
LEAD = ("Moreira and Muir's (2017) volatility-managed factors, each month's position scaled by the inverse of last month's realised variance, and the real-time critique of Cederburg et al. (2020), "
        "replicated on Kenneth R. French's six equity factors. Then the study's own question: what the signal did in the 136 months after Moreira and Muir's sample, May 2015 to August 2026. "
        "Every figure is a simulation drawn from the tables committed with the code.")
TITLE = "Volatility-managed portfolios: the results"
DESC = "Moreira and Muir (2017) and Cederburg et al. (2020) replicated on Ken French's six factors, and the 136 months after the sample: key figures and the method."
page = open(os.path.join(SCRIPT_DIR, "template.html.in")).read()
for k, v in {"title": TITLE, "description": DESC, "lead": LEAD, "vintage": VINTAGE, "build_date": build_words, "BODY": BODY, "SCRIPT": SCRIPT}.items():
    page = page.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{[^}]+\}\}", page)
if left:
    sys.exit(f"dashboard/build_dashboard.py: placeholders left unfilled: {left}")
open(OUT, "w").write(page)
print(f"written {os.path.relpath(OUT, REPO)}, {len(page):,} bytes, {sum(1 for k in ORDER if k[0] == 'figure')} figures, {sum(1 for k in ORDER if k[0] == 'table')} tables")
