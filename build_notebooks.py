"""
Builds the notebooks in notebooks/ from this file and from the modules in src/sq/.

A .ipynb is JSON with outputs and execution counts stored beside the code, so a
hand-edited notebook cannot be reviewed as a diff. The notebooks here are build
artefacts: this script is the source of truth for the prose, and src/sq/ is the
source of truth for the code. Each notebook writes the modules it needs into
src/sq/ with %%writefile cells, so it runs standalone in Colab from a blank
runtime, and the same modules run from the repository checkout.

Run:  python3 build_notebooks.py
Notebooks are written without outputs. Never commit a notebook with outputs.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src" / "sq"
OUT = ROOT / "notebooks"


def _lines(src: str) -> list[str]:
    """Split text into the list-of-strings form a .ipynb expects (each line keeps its newline)."""
    parts = src.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text.strip("\n"))}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": _lines(text.strip("\n"))}


def writefile(relpath: str) -> dict:
    """A cell that writes one module from src/sq/ so the notebook runs from a blank runtime."""
    body = (SRC / relpath).read_text()
    return code(f"%%writefile src/sq/{relpath}\n{body}")


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }


def write(name: str, cells: list[dict]) -> pathlib.Path:
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(notebook(cells), indent=1, ensure_ascii=False) + "\n")
    return path


SETUP = code("""
import os
os.makedirs("src/sq", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
open("src/sq/__init__.py", "w").close()
""")

# ---------------------------------------------------------------------------
# 01: the data
# ---------------------------------------------------------------------------

NB01 = [
    md("""
# 01. The data: Ken French's daily and monthly factor files, downloaded and counted

**Terms used in this notebook.**

| Term | Meaning |
|---|---|
| Factor | the monthly or daily return of one long-short portfolio that captures one source of common movement in stock returns. The six here: the market above cash (Mkt-RF), small minus big firms (SMB), cheap minus expensive firms (HML), past winners minus past losers (Mom), profitable minus unprofitable firms (RMW), and firms that invest little minus firms that invest a lot (CMA) |
| Risk-free rate | the return on a one-month US Treasury bill (RF in French's files) |
| Excess return | a return minus the risk-free rate over the same period. Mkt-RF is the market's return minus the risk-free rate; the other five factors are long-short portfolios, paid for by their own short side, so their returns are excess returns as well |
| Trading day | a day on which the New York Stock Exchange traded. French's daily files have one row per trading day |
| Realised variance | the variance of a factor computed from the daily returns of one month. It is the signal this study evaluates, built in notebook 02 |
| Value-weighted return | the return of a group of firms in which each firm counts in proportion to its market value at the start of the period |
| Decile | one tenth of the stocks, ranked by a characteristic. The ten momentum portfolios rank stocks by their return from twelve months to two months before the portfolio is formed |
| WML | winners minus losers: the top momentum decile's return minus the bottom decile's, the momentum series of Barroso and Santa-Clara (2015) |
| Vintage | the version of French's files on the download date, named by the release of the CRSP database they were built from (202609 is the September 2026 release) |
| Provenance | the record of what was downloaded, when, with its checksum and vintage |
| Sample | the months a comparison runs on. The study uses four, listed below |

**What this notebook does.** It downloads the eight files of Ken French's data library this study reads, records what it downloaded (the date, the address, the SHA-256 checksum of each zip and the CRSP vintage French prints at the top of each file), turns the files into tables of the six factors and of WML, monthly and daily, and counts what is in them: months, trading days, and the months each sample holds.

**Why it comes first.** Every number in the study is computed from these files, and French revises history: a return from 1985 can differ between the file served today and the file Moreira and Muir downloaded in 2015. A replication that misses a published number has to be able to say whether the code or the data moved. The provenance record written here makes that possible, and every later output carries it.

**Which expectations it judges.** None. The six expectations, E1 to E6, are fixed in `src/sq/constants.py` and judged in notebooks 03 to 08. This notebook checks the counts those expectations rest on.

**The papers.** Moreira and Muir (2017), "Volatility-Managed Portfolios", Journal of Finance 72(4), 1611-1644; Cederburg, O'Doherty, Wang and Yan (2020), "On the performance of volatility-managed portfolios", Journal of Financial Economics 138(1), 95-117; Barroso and Santa-Clara (2015), "Momentum has its moments", Journal of Financial Economics 116(1), 111-120. Page numbers below are the journals'.

**What I expect to see, and where it comes from.**

- Eight files, each with a vintage line. On 10 November 2026 the library served vintage 202609, which runs to September 2026; the loader cuts every file at August 2026, the end of the sample fixed in the constants (`SAMPLE_END`), so a later vintage gives the same months.
- Monthly rows to August 2026: **1,202** in the three-factor file (from July 1926), **758** in the five-factor file (from July 1963), **1,196** in the momentum file and in the file of ten momentum portfolios (from January 1927).
- Daily files start on 1 July 1926 (three factors), 1 July 1963 (five factors) and 3 November 1926 (momentum and the ten portfolios), and end on 31 August 2026.
- Trading days per month run from **17 to 27 before June 1952** and from **15 to 23 from 1953 on**, because the daily files carry Saturday trading days until **24 May 1952**, when the New York Stock Exchange stopped trading on Saturdays. No month has fewer than 15 trading days, the level below which a month is flagged (`TRADING_DAYS_FLAG_BELOW`).
- The samples, each counted from the factor's first month with a volatility-managed return (August 1926 for Mkt-RF, SMB and HML, January 1927 for Mom, August 1963 for RMW and CMA; Cederburg et al., Table 1 note, p. 99):
    - Moreira and Muir's sample, to April 2015: **1,065, 1,060 and 621** months, the N their Table I prints (p. 1619). The paper says only "1926 to 2015"; the end in April 2015 is inferred from these three counts, and this notebook confirms that the data hold a return for every one of those months.
    - Cederburg et al.'s sample, to December 2016: **1,085, 1,080 and 641** months (their Table 1 note, p. 99).
    - The months after Moreira and Muir's sample, May 2015 to August 2026: **136** months, the study's own question.
    - Barroso and Santa-Clara's sample: the paper's runs from March 1927 to December 2011 (Table 3, p. 116). French's daily file of the ten momentum portfolios starts on 3 November 1926, and the variance they scale by needs 126 trading days, which are first available at the end of April 1927. The first scaled month is therefore **May 1927**, two months after the paper's, and the sample holds **1,016** months.
"""),
    md("""
## The constants, the published numbers and the loader

Every sample boundary, construction parameter and expectation lives in one module, `src/sq/constants.py`, with its source beside it; the notebooks read these names and never introduce numbers of their own. The published numbers of the three papers live in `src/sq/published.py`, each with its page and table. The loader is `src/sq/french_loader.py`. The cells below write the three modules into the runtime, so that this notebook runs from a blank Colab runtime; in the repository the files are the same text.
"""),
    SETUP,
    writefile("constants.py"),
    writefile("published.py"),
    writefile("french_loader.py"),
    md("""
## Download and record

The loader downloads each file once into `data/french/` and keeps it there; a rerun reads the cached zip and rebuilds its record from the bytes on disk, so the checksum always describes the file actually used. The record goes to `outputs/provenance_french.json`, which every later notebook reads.
"""),
    code("""
import sys
sys.path.insert(0, "src")
import pandas as pd
from sq import constants as C, published as P, french_loader as fl

records = [fl.download(key) for key in C.FRENCH_FILES]
fl.write_provenance(records)
prov = pd.DataFrame(records)[["key", "filename", "vintage_line", "zip_sha256", "zip_bytes", "download_time_local"]]
prov["zip_sha256"] = prov["zip_sha256"].str[:16]
print(prov.to_string(index=False))

vintages = {r["vintage_line"].split("the ")[-1].split(" ")[0] for r in records}
print("vintage(s) in this run:", vintages)
VINTAGE = sorted(vintages)[-1]
"""),
    md("""
## What each file holds, after the cut at August 2026

The table shows each file's first block (the returns), its first and last date and its number of rows. The checks below the table stop the notebook if a count differs from the expectation.
"""),
    code("""
rows = []
for key in C.FRENCH_FILES:
    block = fl.load_monthly(key, 0)
    rows.append({"file": key, "block": block.attrs["title"], "rows": len(block),
                 "first": str(block.index[0]), "last": str(block.index[-1]), "columns": ", ".join(block.columns)})
files = pd.DataFrame(rows)
print(files.to_string(index=False))

n = files.set_index("file")["rows"]
assert n["factors3"] == 1202 and n["factors5"] == 758 and n["momentum"] == 1196 and n["mom10"] == 1196, n
first = files.set_index("file")["first"]
assert first["factors3_daily"] == "1926-07-01" and first["factors5_daily"] == "1963-07-01", first
assert first["momentum_daily"] == "1926-11-03" and first["mom10_daily"] == "1926-11-03", first
assert (files["last"].str[:7] == C.SAMPLE_END).all(), files["last"]
"""),
    md("""
## The study's series

`fl.factors` puts the six factors and the risk-free rate side by side, in decimal returns (1.5 per cent is 0.015), each from the file the constants name: Mkt-RF, SMB and HML from the three-factor file, as both papers use them, RMW and CMA from the five-factor file, Mom from the momentum file. A factor whose file starts later is empty (NaN) before its first date. `fl.wml` takes the value-weighted block of the ten momentum portfolios and subtracts the bottom decile from the top one.
"""),
    code("""
monthly = fl.factors("monthly")
daily = fl.factors("daily")
wml_m = fl.wml("monthly")
wml_d = fl.wml("daily")

summary = pd.DataFrame({
    "first month": {f: str(monthly[f].first_valid_index()) for f in C.FACTORS},
    "months": monthly[list(C.FACTORS)].count(),
    "first trading day": {f: str(daily[f].first_valid_index()) for f in C.FACTORS},
    "trading days": daily[list(C.FACTORS)].count(),
})
summary.loc["WML"] = [str(wml_m.first_valid_index()), wml_m.count(), str(wml_d.first_valid_index()), wml_d.count()]
print(summary.to_string())
"""),
    md("""
## Trading days per month

The realised variance of notebook 02 is built from the trading days of one month, so the number of trading days matters. Each paper treats it in its own way: Moreira and Muir sum over the month's trading days (their equation 2, p. 1616), Cederburg et al. rescale every month to 22 trading days (their equation 4, p. 98), and Barroso and Santa-Clara use the last 126 trading days whatever the month (their equation 5, p. 115). The counts below come from the market's daily series; the cell checks that every other daily file has the same trading days from its own first trading day on (momentum's first month, November 1926, starts on the 3rd).
"""),
    code("""
days = fl.trading_days_per_month(daily["Mkt-RF"].dropna())
saturdays = daily.index[daily.index.to_timestamp().dayofweek == 5]
before = days.loc[:"1952-05"]
after = days.loc["1953-01":]

print("trading days per month before June 1952:", before.min(), "to", before.max())
print("trading days per month from 1953 on:    ", after.min(), "to", after.max())
print("Saturday trading days:", len(saturdays), "the last on", saturdays.max())
print("months with the fewest trading days from 1953 on:")
print(after.nsmallest(3).to_string())

flagged = {}
for f in C.FACTORS:
    s = fl.trading_days_per_month(daily[f].dropna())
    # every daily file has the same trading days as the market's from its own first trading day on
    assert s.equals(days.loc[s.index[0]:s.index[-1]]) or s.iloc[1:].equals(days.loc[s.index[1]:s.index[-1]]), f
    flagged[f] = list(s[s < C.TRADING_DAYS_FLAG_BELOW].index.astype(str))
print("months with fewer than", C.TRADING_DAYS_FLAG_BELOW, "trading days:", flagged)

assert (before.min(), before.max(), after.min(), after.max()) == (17, 27, 15, 23)
assert str(saturdays.max()) == C.LAST_SATURDAY_TRADING_DAY
assert all(len(v) == 0 for v in flagged.values())
days.to_frame().to_csv(f"outputs/trading_days_per_month_{VINTAGE}.csv")
"""),
    md("""
## The four samples

For each factor and each sample the cell counts the months that hold both a monthly return and at least one trading day in the month before, which is what a volatility-managed return needs. The published N of Moreira and Muir's Table I sits beside the count for their sample.
"""),
    code("""
def months_with_signal(f, start, end):
    m = monthly[f].loc[start:end].dropna()
    prior = set(fl.trading_days_per_month(daily[f].dropna()).index + 1)   # months whose previous month has trading days
    return sum(1 for p in m.index if p in prior)

rows = []
for f in C.FACTORS:
    first = C.FACTOR_FIRST_MONTH[f]
    rows.append({
        "factor": f, "first month": first,
        "MM to 2015-04": months_with_signal(f, first, C.MM_SAMPLE_END),
        "MM published N": P.MM_TABLE_I[f][4],
        "COWY to 2016-12": months_with_signal(f, first, C.COWY_SAMPLE_END),
        "after 2015-05 to 2026-08": months_with_signal(f, C.AFTER_START, C.AFTER_END),
    })
samples = pd.DataFrame(rows).set_index("factor")
print(samples.to_string())

assert (samples["MM to 2015-04"] == samples["MM published N"]).all()
assert (samples["COWY to 2016-12"] == pd.Series(C.COWY_EXPECTED_N)).all()
assert (samples["after 2015-05 to 2026-08"] == C.AFTER_EXPECTED_MONTHS).all()
for f in C.FACTORS:
    assert str(monthly[f].first_valid_index()) <= C.FACTOR_FIRST_MONTH[f], f
"""),
    md("""
## Barroso and Santa-Clara's first scaled month

Their variance for month t uses the 126 trading days up to the last trading day of month t-1. The cell finds the first month-end by which WML's daily series has 126 trading days; the first scaled month is the month after it.
"""),
    code("""
wml_days = fl.trading_days_per_month(wml_d.dropna()).cumsum()
ready = wml_days[wml_days >= C.RV_BSC_TRADING_DAYS].index[0]
first_scaled = ready + 1
bsc_months = wml_m.loc[str(first_scaled):C.BSC_SAMPLE_END].dropna()
print("126 trading days first available at the end of", ready, "; first scaled month", first_scaled)
print("months from", first_scaled, "to", C.BSC_SAMPLE_END, ":", len(bsc_months))

assert str(first_scaled) == C.BSC_FIRST_MONTH and len(bsc_months) == C.BSC_EXPECTED_MONTHS
"""),
    md("""
## The counts, written down

The counts go to `outputs/` with the vintage in each file name, beside the provenance record. The tables the write-up cites are copied from `outputs/` into `results/<vintage>/` and committed, so that every number resolves to a file at a named commit.
"""),
    code("""
files.to_csv(f"outputs/files_{VINTAGE}.csv", index=False)
summary.to_csv(f"outputs/series_{VINTAGE}.csv")
samples.to_csv(f"outputs/samples_{VINTAGE}.csv")
print(sorted(os.listdir("outputs")))
"""),
    md("""
## What this notebook established, and what could be wrong

| Check | Expected | Where it comes from |
|---|---|---|
| Monthly rows to August 2026 | 1,202, 758, 1,196, 1,196 | the files' first months and the sample's end |
| Trading days per month | 17 to 27 before June 1952, 15 to 23 from 1953 | Saturday trading until 24 May 1952 |
| Months with fewer than 15 trading days | none | `TRADING_DAYS_FLAG_BELOW` |
| Moreira and Muir's sample to April 2015 | 1,065, 1,060, 621 | their Table I, p. 1619 |
| Cederburg et al.'s sample to December 2016 | 1,085, 1,080, 641 | their Table 1 note, p. 99 |
| Months after the sample | 136 | May 2015 to August 2026 |
| Barroso and Santa-Clara's sample | May 1927 to December 2011, 1,016 months | 126 trading days from 3 November 1926 |

Every assert in the notebook passed if the notebook ran to this cell.

What could be wrong:

- **The end of Moreira and Muir's sample is inferred.** April 2015 reproduces all three published N exactly; a start eight months later for every factor with an end in December 2015 reproduces them too. The inference is written in the constants with the three counts, and notebook 03 reports the computed N beside the published N.
- **The vintage differs from the papers'.** Moreira and Muir downloaded French's files around 2015 and Cederburg et al. around 2017; French has revised history since, so a computed number can miss a published one with the code right. The provenance record says which vintage every later number comes from.
- **WML starts two months later than the paper's.** The difference is two of the paper's 1,018 months and is disclosed wherever E3 is judged.
"""),
]

# ---------------------------------------------------------------------------
# 02: the signal and the positions
# ---------------------------------------------------------------------------

NB02 = [
    md("""
# 02. The signal: last month's realised variance, and the position each construction takes from it

**Terms used in this notebook.**

| Term | Meaning |
|---|---|
| Factor | the monthly or daily return of one long-short portfolio that captures one source of common movement in stock returns: Mkt-RF, SMB, HML, Mom, RMW and CMA, as in notebook 01 |
| Excess return | a return minus the one-month Treasury bill rate over the same period; every factor is one |
| Trading day | a day on which the New York Stock Exchange traded, one row of French's daily files |
| Realised variance | the variance of a factor computed from the daily returns of one month. Last month's realised variance is the signal this study evaluates |
| Position | the multiple of the factor held in a month: a position of 2 doubles every gain and loss of the factor, 0.5 halves them. The papers call a position above 1 leverage |
| Volatility-managed factor | Moreira and Muir's construction: a position of c divided by last month's realised variance, so the position is small after a volatile month and large after a calm one |
| c | the constant of the volatility-managed factor, set so that its standard deviation over the sample equals the original factor's |
| Percentile | the value below which a given share of the months fall: the 95th percentile (P95) is exceeded in 5 months out of 100 |
| Covariance matrix | the table of the variances of two or more return series and the covariances between each pair |
| Mean-variance weights | the amounts of each return series an investor holds who trades off the mean of the portfolio's return against its variance: (1/γ) times the inverse of the covariance matrix times the vector of means |
| γ (gamma) | risk aversion: how much variance the investor gives up for one unit of mean return. A larger γ gives smaller positions |
| Real-time combination | Cederburg, O'Doherty, Wang and Yan's construction: each month, mean-variance weights on the volatility-managed and the original factor, estimated from the months before it only. Its return is S1 |
| Real-time original | the same with the original factor alone. Its return is S2 |
| Training window | the months a real-time estimate is computed from: every month from the factor's first month to the month before the one being invested in |
| Cap | the largest position the real-time constructions may take, 5 in either direction |
| Vintage | the version of French's files on the download date, named by the CRSP release they were built from |
| Provenance | the record of what was downloaded, when, with its checksum and vintage, written to `outputs/provenance_french.json` |

**What this notebook does.** It builds the signal, last month's realised variance, for each of the six factors under the three papers' definitions, and turns it into a position in two ways: Moreira and Muir's volatility-managed factor, on their sample, and Cederburg et al.'s real-time combination, month by month from the end of its first ten-year training window to August 2026. It reports how large the positions are, works one month of each construction by hand, and writes every series to `outputs/`. No return, Sharpe ratio or alpha is computed here.

**Why it comes at this point.** Every later notebook compares returns of positions built here. Before any comparison, the positions themselves have to be right: computed from the months before the one invested in, with each paper's own definition, and of a size a reader can check against the papers' description.

**Which expectations it judges.** None. E6 judges the percentiles of the volatility-managed position against the papers' Table V and Table 1, Panel D, in notebook 08; this notebook reports the 5th, 50th and 95th percentiles and the maximum, which the design names for describing the position.

**The papers.** Moreira and Muir (2017), "Volatility-Managed Portfolios", Journal of Finance 72(4), 1611-1644; Cederburg, O'Doherty, Wang and Yan (2020), "On the performance of volatility-managed portfolios", Journal of Financial Economics 138(1), 95-117; Barroso and Santa-Clara (2015), "Momentum has its moments", Journal of Financial Economics 116(1), 111-120. Page numbers are the journals'.

**The three definitions of the signal.**

- Moreira and Muir, equation 2, p. 1616: each day's return minus the month's mean daily return, squared, summed over the month's trading days. A month with more trading days gives a larger sum at the same daily risk.
- Cederburg et al., equation 4, p. 98: the sum of the squared daily returns, times 22 divided by the month's number of trading days J. Every month is rescaled to 22 trading days.
- Barroso and Santa-Clara, equation 5, p. 115: 21 times the mean squared daily return over the last 126 trading days. The window is fixed in trading days and runs across month ends.

Each comparison with a paper's printed numbers uses that paper's definition (`RV_BY_COMPARISON` in the constants).

**The real-time combination's three numbers, and why each has its value.** All three are Cederburg et al.'s own (Table 5 note and pp. 106-107), so the replication matches their baseline.

- The training window starts at 120 months (`REALTIME_K`), ten years, and grows by one month each month (an expanding window). Ten years leaves most of the sample for investing; Cederburg et al. report that longer starting windows and rolling windows do not change their conclusion (Table 7, p. 110).
- γ = 5 (`REALTIME_GAMMA`) is the risk aversion they use throughout; it scales every position by the same factor, so it changes the size of S1 and S2 and leaves their Sharpe ratios unchanged as long as the cap does not bind.
- The cap of 5 (`REALTIME_LEVERAGE_CAP`), applied by truncating the position at 5 or at -5. Mean-variance weights estimated from a window can be extreme, and the cap keeps the months with extreme estimates from dominating the result (p. 107).

**What I expect to see, and where it comes from.**

- No month below 15 trading days for any factor (notebook 01).
- For the market, the ratio of Cederburg et al.'s realised variance to Moreira and Muir's is close to 22 divided by one less than the month's trading days, 22 / (J - 1). Two things set it. Cederburg et al. rescale the sum of squares to 22 trading days, which gives 22 / J. Moreira and Muir subtract the month's own mean before squaring, and a mean estimated from the same J days absorbs on average one day's worth of variation: with 21 trading days, the sum of squared deviations from the month's mean is on average 20/21 of the sum of squares. Together, 22 / J times J / (J - 1) is 22 / (J - 1): a median near **0.94** before June 1952 (22 / 23.5, with 24.5 trading days on average) and near **1.10** from 1953 (22 / 20.0, with 21.0).
- The volatility-managed position on Moreira and Muir's sample has a median near 1, because c is set so that the managed factor's standard deviation equals the original's, and a long right tail: for every factor the 95th percentile is more than twice the median, as the published percentiles imply (Moreira and Muir's Table V gives the market's 90th percentile as 2.64 against a median of 0.93, p. 1626). The 5th, 50th and 95th percentiles and the maximum are reported for each factor.
- The worked month: on 19 October 1987 the market had its largest one-day fall since 1926. October's realised variance is the largest of the 1980s, so the volatility-managed position for November 1987 is a small fraction of the median position.
- The real-time combination's first position is in the 121st month of each factor: **August 1936** for Mkt-RF, SMB and HML, **January 1937** for Mom and **August 1973** for RMW and CMA. To August 2026 that gives **1,081**, **1,076** and **637** months with a position.
- The real-time position does not depend on c: multiplying the managed factor by any constant divides its mean-variance weight by the same constant, so the product x_sigma times c, and the position, stay the same. The notebook checks it on one month.
"""),
    md("""
## How this notebook is organised

1. The modules are written into the runtime and the factors are loaded.
2. The signal: the three definitions for the six factors, compared for the market, and the months below 15 trading days.
3. A worked month: October 1987, by hand.
4. The volatility-managed factor on Moreira and Muir's sample: c and the size of the position.
5. The real-time combination: one month worked in full, then the positions of every month to August 2026.
6. A figure of the market's signal and both positions.
7. The outputs, and what could be wrong.
"""),
    SETUP,
    writefile("constants.py"),
    writefile("french_loader.py"),
    writefile("managed.py"),
    code("""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from sq import constants as C, french_loader as fl, managed as M

records = [fl.download(key) for key in C.FRENCH_FILES]
fl.write_provenance(records)
VINTAGE = sorted({r["vintage_line"].split("the ")[-1].split(" ")[0] for r in records})[-1]
print("vintage:", VINTAGE)

monthly = fl.factors("monthly")
daily = fl.factors("daily")
pd.set_option("display.width", 160)
"""),
    md("""
## 2. The signal

The cell computes each definition for each factor from its daily returns. Each value belongs to the month whose trading days it was built from; the position for month t uses the value of month t-1, which `M.lagged` puts on month t.
"""),
    code("""
rv = {}
for f in C.FACTORS:
    d = daily[f].dropna()
    rv[f] = pd.DataFrame({"mm": M.rv_mm(d), "cowy": M.rv_cowy(d), "bsc": M.rv_bsc(d)})

counts = pd.DataFrame({f: {"months": len(rv[f]), "first": str(rv[f].index[0]), "last": str(rv[f].index[-1]),
                           "first Barroso-Santa-Clara value": str(rv[f]["bsc"].first_valid_index())} for f in C.FACTORS}).T
print(counts.to_string())

days = fl.trading_days_per_month(daily["Mkt-RF"].dropna())
ratio = rv["Mkt-RF"]["cowy"] / rv["Mkt-RF"]["mm"]
print()
print("market, Cederburg et al. over Moreira and Muir, median before June 1952:", round(ratio.loc[:"1952-05"].median(), 3),
      " (22 / (mean trading days - 1):", round(22 / (days.loc[:"1952-05"].mean() - 1), 3), ")")
print("market, Cederburg et al. over Moreira and Muir, median from 1953:      ", round(ratio.loc["1953-01":].median(), 3),
      " (22 / (mean trading days - 1):", round(22 / (days.loc["1953-01":].mean() - 1), 3), ")")
print("correlation of the logs of the two definitions, market:", round(np.log(rv["Mkt-RF"]["cowy"]).corr(np.log(rv["Mkt-RF"]["mm"])), 4))

flagged = {f: int((fl.trading_days_per_month(daily[f].dropna()) < C.TRADING_DAYS_FLAG_BELOW).sum()) for f in C.FACTORS}
print("months below", C.TRADING_DAYS_FLAG_BELOW, "trading days:", flagged)
assert all(v == 0 for v in flagged.values())
"""),
    md("""
## 3. A worked month: October 1987

The market's daily returns in October 1987, the sum Moreira and Muir's definition takes, and the position the volatility-managed factor holds in November 1987. The constant c comes from Moreira and Muir's sample, section 4 of this notebook computes it for every factor.
"""),
    code("""
oct87 = daily["Mkt-RF"].loc["1987-10-01":"1987-10-31"]
by_hand = ((oct87 - oct87.mean()) ** 2).sum()
print(len(oct87), "trading days; largest one-day fall:", round(oct87.min() * 100, 2), "per cent on", oct87.idxmin())
print("largest one-day fall since 1926:", daily["Mkt-RF"].idxmin())
print("mean daily return:", round(oct87.mean() * 100, 3), "per cent")
print("realised variance, Moreira and Muir, by hand:", round(by_hand, 6), " from the module:", round(rv["Mkt-RF"].loc["1987-10", "mm"], 6))
assert abs(by_hand - rv["Mkt-RF"].loc["1987-10", "mm"]) < 1e-15

mkt_mm, c_mkt = M.volatility_managed(monthly["Mkt-RF"], rv["Mkt-RF"]["mm"], C.FACTOR_FIRST_MONTH["Mkt-RF"], C.MM_SAMPLE_END)
print("c on Moreira and Muir's sample:", round(c_mkt, 6))
print("position in November 1987: c / RV(October) =", round(c_mkt, 6), "/", round(by_hand, 6), "=", round(mkt_mm.loc["1987-11", "weight"], 3))
print("median position on the sample:", round(mkt_mm["weight"].median(), 3))
print("realised variance of October 1987 is the largest from 1980 to 1989:", rv["Mkt-RF"]["mm"].loc["1980-01":"1989-12"].idxmax() == pd.Period("1987-10", "M"))
"""),
    md("""
## 4. The volatility-managed factor on Moreira and Muir's sample

For each factor, on its months from its first month to April 2015: c, and the 5th, 50th and 95th percentiles and the maximum of the position c / RV(t-1), with Moreira and Muir's definition of the signal.
"""),
    code("""
rows, vm = [], {}
for f in C.FACTORS:
    df, c = M.volatility_managed(monthly[f], rv[f]["mm"], C.FACTOR_FIRST_MONTH[f], C.MM_SAMPLE_END)
    vm[f] = df
    rows.append({"factor": f, "months": len(df), "c": c, **M.percentiles(df["weight"])})
vm_table = pd.DataFrame(rows).set_index("factor")
print(vm_table.round(4).to_string())
assert (vm_table["months"] == pd.Series(C.MM_EXPECTED_N)).all()
print("95th percentile over the median:", (vm_table["P95"] / vm_table["P50"]).round(2).to_dict())
for f in C.FACTORS:
    assert abs(vm[f]["managed"].std() - vm[f]["f"].std()) < 1e-12
"""),
    md("""
## 5. The real-time combination

**One month worked in full.** The market's first month with a position, August 1936. The training window holds the 120 months from August 1926 to July 1936. The cell computes c for the window, the means and the covariance matrix of the managed and the original factor over the window, the mean-variance weights, and the position. It then repeats the weights with c multiplied by 7 to show that the position does not move.
"""),
    code("""
f_m, rv_m = monthly["Mkt-RF"], rv["Mkt-RF"]["cowy"]
window = pd.period_range(C.FACTOR_FIRST_MONTH["Mkt-RF"], "1936-07", freq="M")
f_w = f_m.loc[window].to_numpy()
raw_w = f_w / M.lagged(rv_m).loc[window].to_numpy()
c_t = f_w.std(ddof=1) / raw_w.std(ddof=1)
X = np.column_stack([c_t * raw_w, f_w])
print("window:", len(window), "months; c =", round(c_t, 6))
print("means (managed, original), per cent a month:", (X.mean(axis=0) * 100).round(3))
print("covariance matrix:"); print(np.cov(X, rowvar=False).round(6))
x_sigma, x = M.mean_variance_weights(X, C.REALTIME_GAMMA)
y = x_sigma * c_t / rv_m.loc["1936-07"] + x
print("weights: managed", round(x_sigma, 4), " original", round(x, 4))
print("position in August 1936: x_sigma * c / RV(July 1936) + x =", round(y, 4), "; after the cap:", round(float(np.clip(y, -5, 5)), 4))
xs7, x7 = M.mean_variance_weights(np.column_stack([7 * c_t * raw_w, f_w]), C.REALTIME_GAMMA)
print("with c times 7: managed weight", round(xs7, 4), "; x_sigma * c unchanged:", np.isclose(xs7 * 7 * c_t, x_sigma * c_t))
assert np.isclose(xs7 * 7 * c_t, x_sigma * c_t) and np.isclose(x7, x)

rt_mkt = M.real_time(f_m, rv_m, C.FACTOR_FIRST_MONTH["Mkt-RF"], C.SAMPLE_END)
assert np.isclose(rt_mkt.loc["1936-08", "y"], float(np.clip(y, -5, 5)))
"""),
    md("""
**Every month, every factor.** The real-time combination and the real-time original from the end of the first training window to August 2026, with Cederburg et al.'s definition of the signal. The table gives the first month with a position, the number of months, the percentiles and the maximum of S1's position, the share of months in which it is negative (the combination is then short the factor, holding minus the factor's return), the share in which the cap binds, and the median position of S2.
"""),
    code("""
rows, rt = [], {}
for f in C.FACTORS:
    out = M.real_time(monthly[f], rv[f]["cowy"], C.FACTOR_FIRST_MONTH[f], C.SAMPLE_END)
    rt[f] = out
    rows.append({"factor": f, "first month": str(out.index[0]), "months": len(out), **M.percentiles(out["y"]),
                 "share below 0": (out["y"] < 0).mean(), "share at cap": out["at_cap"].mean(), "S2 median": out["y2"].median()})
rt_table = pd.DataFrame(rows).set_index("factor")
print(rt_table.round(4).to_string())
assert list(rt_table["first month"]) == ["1936-08"] * 3 + ["1937-01"] + ["1973-08"] * 2
assert list(rt_table["months"]) == [1081] * 3 + [1076] + [637] * 2
"""),
    md("""
## 6. The market's signal and both positions

Three panels, one per series. The first shows the market's realised volatility, the square root of 12 times Moreira and Muir's realised variance, in per cent a year. The second shows the volatility-managed factor's position on Moreira and Muir's sample, on a logarithmic scale so that a position of 0.5 and one of 2 sit at the same distance from 1; the position is always above 0. The third shows the real-time combination's position from August 1936 on an ordinary scale, because it can be negative, with the cap at 5 and -5 as dashed lines.
"""),
    code("""
import matplotlib.pyplot as plt

NAVY, GREY, RULE, LIMIT = "#16213a", "#8d9ab0", "#d6d9de", "#5d6470"
vol = np.sqrt(12 * rv["Mkt-RF"]["mm"]) * 100
fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 9), sharex=True, gridspec_kw={"hspace": 0.35})
fig.patch.set_facecolor("white")
a1.plot(vol.index.to_timestamp(), vol.values, color=NAVY, linewidth=0.8)
a1.set_title("Market realised volatility, % a year, July 1926 to August 2026", loc="left", fontsize=11, color=NAVY)
a2.plot(vm["Mkt-RF"].index.to_timestamp(), vm["Mkt-RF"]["weight"], color=NAVY, linewidth=0.8)
a2.set_yscale("log")
a2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
a2.axhline(1, color=RULE, linewidth=0.8)
a2.set_title("Volatility-managed position, multiple of the factor, log scale, August 1926 to April 2015", loc="left", fontsize=11, color=NAVY)
a3.plot(rt["Mkt-RF"].index.to_timestamp(), rt["Mkt-RF"]["y"], color=NAVY, linewidth=0.8)
a3.axhline(0, color=RULE, linewidth=0.8)
for level in (C.REALTIME_LEVERAGE_CAP, -C.REALTIME_LEVERAGE_CAP):
    a3.axhline(level, color=LIMIT, linewidth=1.0, linestyle="--")
a3.text(rt["Mkt-RF"].index[-1].to_timestamp(), C.REALTIME_LEVERAGE_CAP, " cap", va="bottom", fontsize=9, color=LIMIT)
a3.set_ylim(-5.8, 5.8)
a3.set_title("Real-time combination's position, multiple of the factor, August 1936 to August 2026", loc="left", fontsize=11, color=NAVY)
for a in (a1, a2, a3):
    a.set_facecolor("white")
    a.spines[["top", "right"]].set_visible(False)
    a.tick_params(labelsize=9)
plt.show()
"""),
    md("""
## 7. The outputs

The signal of every factor under the three definitions, the volatility-managed positions on Moreira and Muir's sample, the real-time positions and returns to August 2026, and the two summary tables, each with the vintage in its file name.
"""),
    code("""
pd.concat(rv, axis=1).to_csv(f"outputs/realised_variance_{VINTAGE}.csv")
pd.concat({f: vm[f][["f", "rv_lag", "weight", "managed"]] for f in C.FACTORS}, axis=1).to_csv(f"outputs/volatility_managed_mm_sample_{VINTAGE}.csv")
pd.concat({f: rt[f] for f in C.FACTORS}, axis=1).to_csv(f"outputs/real_time_{VINTAGE}.csv")
vm_table.to_csv(f"outputs/position_volatility_managed_{VINTAGE}.csv")
rt_table.to_csv(f"outputs/position_real_time_{VINTAGE}.csv")
print(sorted(os.listdir("outputs")))
"""),
    md("""
## What this notebook established, and what could be wrong

| Check | Expected | Where it comes from |
|---|---|---|
| Months below 15 trading days | none | notebook 01 |
| Market, Cederburg et al.'s signal over Moreira and Muir's, median | near 0.94 before June 1952, near 1.10 from 1953 | 22 / (J - 1): the rescaling to 22 days and the month's own mean |
| Volatility-managed position | median near 1, 95th percentile more than twice the median | c sets the managed factor's standard deviation equal to the original's; the published percentiles |
| October 1987 | the largest realised variance of the 1980s, a small November position | the fall of 19 October 1987 |
| Real-time combination, first month and months to August 2026 | August 1936 and 1,081 for Mkt-RF, SMB, HML; January 1937 and 1,076 for Mom; August 1973 and 637 for RMW, CMA | a training window of 120 months |
| The real-time position and c | unchanged when c is multiplied by 7 | the weights scale by the inverse of c |

Every assert in the notebook passed if the notebook ran to this cell. The percentiles of the two positions are reported with no pass or fail; E6 judges the volatility-managed position's percentiles in notebook 08.

What could be wrong:

- **Moreira and Muir's equation 2 is written for a 22-day month.** The module removes the month's own mean, the sum of its daily returns divided by its number of trading days. With the mean as small as it is next to the daily swings, the choice moves the signal by little; notebook 03 shows whether the computed table matches theirs.
- **The cap is applied by truncation.** Cederburg et al. state the constraint, |y_t| at most 5 (p. 107), without saying how a larger position is brought back to it; truncating at 5 is the direct reading. The share of months at the cap says how often the choice matters.
- **The vintage differs from the papers'.** French's history has been revised since 2015 and 2017. The provenance record says which vintage every number comes from.
"""),
]


if __name__ == "__main__":
    for name, cells in (("01_french_loader.ipynb", NB01), ("02_realised_variance.ipynb", NB02)):
        print(write(name, cells))
