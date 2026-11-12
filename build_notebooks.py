"""
Builds the notebooks in notebooks/ from this file and from the modules in src/sq/.

A .ipynb is JSON with outputs and execution counts stored beside the code, so a
hand-edited notebook cannot be reviewed as a diff. The notebooks here are build
artefacts: this script is the source of truth for the prose, and src/sq/ is the
source of truth for the code. Each notebook writes the modules it needs into
src/sq/ with %%writefile cells, so it runs standalone in Colab from a blank
runtime, and the same modules run from the repository checkout.

Run:  python3 build_notebooks.py [03 04 ...]
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

# ---------------------------------------------------------------------------
# 03: Moreira and Muir's Table I
# ---------------------------------------------------------------------------

NB03 = [
    md("""
# 03. Moreira and Muir's Table I on their sample: every published number beside the computed one (E1)

**Terms used in this notebook.**

| Term | Meaning |
|---|---|
| Factor | the monthly return of one long-short portfolio that captures one source of common movement in stock returns: Mkt-RF, SMB, HML, Mom, RMW and CMA |
| Realised variance | the variance of a factor computed from the daily returns of one month; last month's is the signal |
| Volatility-managed factor | Moreira and Muir's construction: the factor's return times c divided by last month's realised variance, built in notebook 02 |
| Regression | the straight line through the months that best predicts one series from another, here the volatility-managed factor from the original factor, fitted by least squares (the line that makes the sum of squared misses smallest) |
| Beta | the slope of that line: how much the volatility-managed factor moves, on average, when the original factor moves by 1 |
| Alpha | the intercept of that line: the average monthly return of the volatility-managed factor that the original factor does not account for. Here it is a property of the regression and nothing more |
| Residual | the month's miss: the volatility-managed return minus the line's prediction |
| RMSE | the standard deviation of the residuals, with the two estimated coefficients taken into account (the sum of squared residuals divided by N - 2, square-rooted) |
| N | the number of months in the regression |
| Standard error | how far an estimate would typically move if the same months were drawn again; a small one means a precise estimate |
| White standard error | a standard error that allows the size of the residuals to change from month to month (White 1980). Moreira and Muir's Table I uses it |
| Newey-West standard error | a standard error that also allows each month's residual to be correlated with the previous months' (Newey and West 1987), here with 12 months |
| t-statistic | the estimate divided by its standard error |
| 5 per cent significance | a t-statistic further from 0 than 1.96. If the true alpha were 0, a t-statistic that far out would occur in 5 months out of 100 by chance |
| Appraisal ratio | alpha divided by the RMSE: the extra return per unit of the risk the original factor does not explain |
| Excess return | a return minus the one-month Treasury bill rate over the same period; every factor is one |
| Sharpe ratio | the average excess return divided by its standard deviation |
| Annualised | turned from a monthly figure into a yearly one: means times 12, standard deviations and Sharpe ratios times the square root of 12 |
| Verdict | met or not met: the result of an expectation, read from levels fixed before the code ran |
| Vintage | the version of French's files on the download date, named by the CRSP release they were built from |

**What this notebook does.** It builds the volatility-managed version of each of the six factors on Moreira and Muir's sample, regresses it on the original factor, and puts every number of their Table I (p. 1619) beside the computed one: beta, alpha, the standard error of alpha, N, R² and RMSE. It computes the appraisal ratio from both, and the market's volatility-managed Sharpe ratio for comparison with their Table V (p. 1626). It then judges E1.

**Why it comes at this point.** This is the paper's main table. A replication that matches it shows that the data, the signal and the construction of notebooks 01 and 02 are those of the paper; every later notebook builds on them. A replication that misses it stops the study until the miss is explained.

**The expectation it judges: E1**, fixed in `src/sq/constants.py` before this notebook's code was written:

1. On Moreira and Muir's sample (each factor's first month to April 2015), for at least five of the six factors:
    - the alpha's sign matches Table I's;
    - its 5 per cent significance category matches Table I's, with White standard errors, the paper's own;
    - the alpha lies within one published standard error of the published alpha;
    - the appraisal ratio, computed from Table I's alpha and RMSE with footnote 11's annualisation (p. 1620), lies within 0.05 of the paper's figure.
2. For the market, the volatility-managed Sharpe ratio also lies within 0.05 of 0.52 (Table V, Panel A), and the market counts as matching only if it does.

**Why these levels.** They are the replication criterion fixed on 6 September 2026, before the study's design: the sign and significance of the alpha, one standard error, and a margin of 0.05 on a ratio. French has revised his data since Moreira and Muir downloaded it, so exact equality is not expected; five of six lets one factor miss on a revised series, and a miss is reported, never chased. The paper prints a Sharpe ratio for the market only, so the third comparison for every factor is the appraisal ratio, which Table I gives through alpha and RMSE. The 5 per cent line is 1.96, from the normal distribution, as the paper's own stars use it.

**What I expect to see, and where it comes from.** E1 met. The published Table I, Panel A, for the six factors (alpha and its standard error in per cent a year, from monthly returns times 12):

| | Mkt-RF | SMB | HML | Mom | RMW | CMA |
|---|---|---|---|---|---|---|
| beta | 0.61 | 0.62 | 0.57 | 0.47 | 0.62 | 0.68 |
| alpha | 4.86 | -0.58 | 1.97 | 12.51 | 2.44 | 0.38 |
| standard error of alpha | 1.56 | 0.91 | 1.02 | 1.71 | 0.83 | 0.67 |
| t-statistic | 3.12 | -0.64 | 1.93 | 7.32 | 2.94 | 0.57 |
| N | 1,065 | 1,065 | 1,065 | 1,060 | 621 | 621 |
| R² | 0.37 | 0.38 | 0.32 | 0.22 | 0.38 | 0.46 |
| RMSE | 51.39 | 30.44 | 34.92 | 50.37 | 20.16 | 17.55 |
| appraisal ratio (alpha / RMSE times the square root of 12) | 0.33 | -0.07 | 0.20 | 0.86 | 0.42 | 0.08 |

Three things to watch. HML's published t-statistic, 1.93, sits 0.03 below the 1.96 line, so a small change in its alpha or standard error moves it across. SMB's and CMA's alphas are small next to their standard errors, so their sign can differ while the alpha still lies within one standard error. The N are known to match from notebook 01.
"""),
    md("""
## How this notebook is organised

1. The modules are written into the runtime and the volatility-managed factors are built on Moreira and Muir's sample.
2. The regressions: the computed Table I.
3. One factor worked from monthly numbers to the paper's units.
4. The computed and the published numbers side by side, and E1 judged.
5. White and Newey-West standard errors compared.
6. The outputs, the summary and what could be wrong.
"""),
    SETUP,
    writefile("constants.py"),
    writefile("published.py"),
    writefile("french_loader.py"),
    writefile("managed.py"),
    writefile("regression.py"),
    writefile("verdicts.py"),
    code("""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from sq import constants as C, published as P, french_loader as fl, managed as M, regression as R, verdicts as V

records = [fl.download(key) for key in C.FRENCH_FILES]
fl.write_provenance(records)
VINTAGE = sorted({r["vintage_line"].split("the ")[-1].split(" ")[0] for r in records})[-1]
print("vintage:", VINTAGE)
monthly = fl.factors("monthly")
daily = fl.factors("daily")
pd.set_option("display.width", 200)

vm = {}
for f in C.FACTORS:
    rv = M.rv_mm(daily[f].dropna())               # Moreira and Muir's definition, equation 2
    vm[f], _ = M.volatility_managed(monthly[f], rv, C.FACTOR_FIRST_MONTH[f], C.MM_SAMPLE_END)
print({f: len(vm[f]) for f in C.FACTORS})
"""),
    md("""
## 2. The regressions

Each column regresses the volatility-managed factor on the original factor over the factor's months on Moreira and Muir's sample, in the paper's units.
"""),
    code("""
computed = pd.DataFrame({f: R.table_i_row(vm[f]["managed"], vm[f]["f"]) for f in C.FACTORS}).T
print(computed[["beta", "beta_se_white", "alpha", "alpha_se_white", "N", "R2", "RMSE", "appraisal"]].astype(float).round(3).T.to_string())
"""),
    md("""
## 3. The market, from monthly numbers to the paper's units

The regression runs on monthly decimal returns. Table I multiplies alpha, its standard error and the RMSE by 12 and writes them in per cent; the appraisal ratio, alpha over RMSE, is then a monthly ratio, and footnote 11 multiplies it by the square root of 12 to make it yearly.
"""),
    code("""
fit = R.ols(vm["Mkt-RF"]["managed"].to_numpy(), vm["Mkt-RF"]["f"].to_numpy())
print("monthly alpha:", round(fit["alpha"], 6), " times 12, in per cent:", round(fit["alpha"] * 1200, 3))
print("monthly standard error (White):", round(fit["alpha_se_white"], 6), " times 12, in per cent:", round(fit["alpha_se_white"] * 1200, 3))
print("monthly RMSE:", round(fit["rmse"], 6), " times 12, in per cent:", round(fit["rmse"] * 1200, 3))
print("appraisal ratio: alpha / RMSE * sqrt(12) =", round(fit["alpha"] / fit["rmse"] * np.sqrt(12), 4))
print("Sharpe ratio, volatility-managed:", round(R.sharpe(vm["Mkt-RF"]["managed"]), 4), " original:", round(R.sharpe(vm["Mkt-RF"]["f"]), 4))
"""),
    md("""
## 4. Beside the published numbers, and E1 judged

The first table puts the numbers E1 judges beside the paper's, with each comparison's result. The second gives the numbers E1 does not judge (beta, R² and RMSE) beside the paper's, for the reader.
"""),
    code("""
e1_table, e1_met = V.e1(computed)
print(e1_table.T.to_string())
print()
others = pd.DataFrame({
    "beta published": {f: P.MM_TABLE_I[f][0] for f in C.FACTORS}, "beta computed": computed["beta"].astype(float),
    "R2 published": {f: P.MM_TABLE_I[f][5] for f in C.FACTORS}, "R2 computed": computed["R2"].astype(float),
    "RMSE published": {f: P.MM_TABLE_I[f][6] for f in C.FACTORS}, "RMSE computed": computed["RMSE"].astype(float),
})
print(others.round(3).T.to_string())
print()
n_match = int(e1_table["factor matches"].sum())
print(f"E1: {'MET' if e1_met else 'NOT MET'}. {n_match} of 6 factors match on every comparison; at least {C.E1_MIN_FACTORS} required.")
"""),
    md("""
## 5. White and Newey-West standard errors

E1 uses White's standard error because Table I does. The study's later tests (E4 to E6) use Newey and West's, which also allows a month's residual to be correlated with the 12 months before it. Where the residuals of neighbouring months move together, a run of months carries less independent information than its count suggests, and the Newey-West standard error is larger.
"""),
    code("""
se = computed[["alpha", "alpha_se_white", "alpha_se_nw"]].astype(float)
se["t White"] = se["alpha"] / se["alpha_se_white"]
se["t Newey-West"] = se["alpha"] / se["alpha_se_nw"]
se["Newey-West over White"] = se["alpha_se_nw"] / se["alpha_se_white"]
print(se.round(3).to_string())
"""),
    md("""
## 6. The outputs, the summary, and what could be wrong

The computed Table I, the E1 comparison and the verdict go to `outputs/` with the vintage in each name.
"""),
    code("""
computed.to_csv(f"outputs/mm_table_i_computed_{VINTAGE}.csv")
e1_table.to_csv(f"outputs/e1_comparison_{VINTAGE}.csv")
pd.DataFrame([{"expectation": "E1", "factors matching": n_match, "required": C.E1_MIN_FACTORS,
               "verdict": "met" if e1_met else "not met", "vintage": VINTAGE}]).to_csv(f"outputs/e1_verdict_{VINTAGE}.csv", index=False)

summary = pd.DataFrame([{
    "expectation": "E1: Moreira and Muir's Table I on their sample",
    "result": f"{n_match} of 6 factors match on sign, 5% category, alpha within one se, appraisal ratio within 0.05"
              f"; market Sharpe ratio {computed.loc['Mkt-RF', 'sharpe_managed']:.3f} against 0.52",
    "verdict": "met" if e1_met else "not met",
}]).set_index("expectation")
print(summary.to_string())
print(sorted(os.listdir("outputs")))
"""),
    md("""
What could be wrong, and where each point is tested:

- **French's data have been revised since the paper.** A computed alpha can differ from the published one with the code right. The size of the revision is the difference between the two columns; the comparison of the same construction on Cederburg et al.'s later download (their Table 1, to December 2016) in notebook 04 gives a second reading on a second vintage.
- **The signal's definition.** Moreira and Muir's equation 2 is written for a 22-day month and the module removes the month's own mean (notebook 02). The match of the RMSE and the appraisal ratio is the test: a different signal would change the managed series and both numbers with it.
- **Significance rests on a t-statistic, which assumes the estimate is close to normally distributed.** Notebook 06 tests the same gain with Ledoit and Wolf's bootstrap, which does not assume it, and E4 asks whether the two verdicts agree for at least five of the six factors.
- **The alpha is a property of the regression.** It says the volatility-managed factor earned more than its beta times the original factor over these months. Whether an investor could have captured it is the subject of notebook 04, and whether it survives trading costs that of notebook 08.
"""),
]


# ---------------------------------------------------------------------------
# 04: Cederburg et al. on their sample (E2)
# ---------------------------------------------------------------------------

NB04 = [
    md("""
# 04. Cederburg, O'Doherty, Wang and Yan's Tables 1 and 5 on their sample: the real-time critique (E2)

**Terms used in this notebook.**

| Term | Meaning |
|---|---|
| Factor | the monthly return of one long-short portfolio that captures one source of common movement in stock returns: Mkt-RF, SMB, HML, Mom, RMW and CMA |
| Excess return | a return minus the one-month Treasury bill rate over the same period; every factor is one |
| Realised variance | the variance of a factor computed from the daily returns of one month. Here Cederburg et al.'s definition (equation 4, p. 98): 22 divided by the month's number of trading days, times the sum of the squared daily returns |
| Volatility-managed factor | the factor's return times c divided by last month's realised variance, built in notebook 02; c gives it the original factor's standard deviation over the sample |
| Sharpe ratio | the average excess return divided by its standard deviation, annualised: times the square root of 12 |
| Alpha | the intercept of the regression of the volatility-managed factor on the original factor: the average return the original factor does not account for (notebook 03) |
| Covariance matrix | the table of the variances of two or more return series and the covariances between each pair |
| Mean-variance weights | the amounts of each return series held by an investor who trades the mean of the portfolio's return against its variance: (1/γ) times the inverse of the covariance matrix times the vector of means, with γ, the risk aversion, equal to 5 |
| Training period | the first 120 months of a factor's sample. The real-time strategies hold no position in them |
| Out-of-sample period | the months after the training period, to December 2016: the months on which every strategy of Table 5 is judged |
| Real-time combination (S1) | each month, mean-variance weights on the volatility-managed and the original factor, estimated from every earlier month only, turned into one position in the factor and capped at 5 in either direction (notebook 02) |
| Real-time original (S2) | the original factor alone, held each month at (1/γ) times its mean over its variance, both estimated from every earlier month only, under the same cap |
| Ex post optimal combination (S3) | one pair of mean-variance weights on the volatility-managed and the original factor, set with the means and covariance of the whole out-of-sample period and held in every month of it. No investor could have held it, since it uses the months it is judged on |
| Cap | the largest position the real-time strategies may take, 5 in either direction |
| Jobson-Korkie test | a test that two return series over the same months have the same Sharpe ratio (Jobson and Korkie 1981, with the correction of Memmel 2003), as Cederburg et al. use it (p. 99) |
| p-value | the probability of a difference at least as far from 0 as the one computed, if the two true Sharpe ratios were equal |
| 5 per cent significance | a p-value below 0.05 |
| Verdict | met or not met: the result of an expectation, read from levels fixed before the code ran |
| Vintage | the version of French's files on the download date, named by the CRSP release they were built from |
| Diagnostic | a number computed after a verdict to read its cause. It carries no verdict and changes no level |
| Internet Archive | a public library of copies of web pages and files taken on past dates, at web.archive.org |

**What this notebook does.** It builds, on Cederburg et al.'s sample and with their definition of the signal, the volatility-managed version of each factor (their Table 1, p. 99) and the three strategies of their Table 5, Panel A (p. 106): the real-time combination S1, the real-time original S2 and the ex post optimal combination S3. It puts every computed Sharpe ratio beside the published one, tests the differences with the Jobson-Korkie test, and judges E2. It closes with the cause of the result and two diagnostics.

**Why it comes at this point.** Notebook 03 replicated Moreira and Muir's Table I: the volatility-managed factor has a positive alpha against the original, so a mix of the two had a higher Sharpe ratio than the original alone, with weights chosen after seeing every month. Cederburg et al. ask whether an investor could have chosen those weights at the time. This study uses their real-time combination on the months after the papers' samples (E5), so their published answer is replicated first.

**The expectation it judges: E2**, fixed in `src/sq/constants.py` before this notebook's code was written. On Cederburg et al.'s sample (August 1926, January 1927 or August 1963 to December 2016), for each of the six factors:

1. (i) the original and the volatility-managed Sharpe ratios lie within 0.05 of their Table 1 (p. 99);
2. (ii) S1 and S2 lie within 0.05 of Table 5, Panel A (p. 106);
3. (iii) S1 minus S2 has the published sign for at least five of the six, and the only difference significant at 5 per cent by the Jobson-Korkie test is momentum's, as published;
4. (iv) S1 minus S3 lies within 0.05 of the published figure for all six.

E2 is met when all four clauses hold. All twenty-four comparisons, four for each factor, are reported, whatever the count.

**Why these levels.** The critique's baseline is a real-time combination of the volatility-managed and the original factor (section 4.3, pp. 106-107): the constant c alone does not move a Sharpe ratio (Moreira and Muir, footnote 6, p. 1616; Cederburg et al., p. 98), and the weights of the combination are what an investor cannot know in advance. A margin of 0.05 on a Sharpe ratio is the replication criterion fixed on 6 September 2026, as in E1. Clause (iii) asks for the published sign and the published significance, the paper's own reading of its table.

**What I expect to see, and where it comes from.** E2 met. The published Sharpe ratios, annualised, with the Jobson-Korkie p-values of the differences in brackets:

| | Mkt-RF | SMB | HML | Mom | RMW | CMA |
|---|---|---|---|---|---|---|
| original (Table 1) | 0.42 | 0.23 | 0.40 | 0.48 | 0.38 | 0.53 |
| volatility-managed (Table 1) | 0.51 | 0.08 | 0.38 | 0.99 | 0.51 | 0.40 |
| S1, real-time combination (Table 5) | 0.42 | 0.14 | 0.38 | 0.92 | 0.44 | 0.52 |
| S2, real-time original | 0.46 | 0.19 | 0.43 | 0.49 | 0.31 | 0.56 |
| S1 minus S2 | -0.04 (0.64) | -0.06 (0.37) | -0.06 (0.41) | 0.44 (0.00) | 0.13 (0.53) | -0.03 (0.20) |
| S3, ex post optimal combination | 0.53 | 0.26 | 0.50 | 0.99 | 0.58 | 0.64 |
| S1 minus S3 | -0.11 (0.01) | -0.12 (0.14) | -0.12 (0.08) | -0.07 (0.07) | -0.14 (0.37) | -0.11 (0.00) |

Table 1 runs from each factor's first month to December 2016: 1,085 months for the market, SMB and HML, 1,080 for momentum, 641 for RMW and CMA. Table 5 runs over each factor's out-of-sample period, which starts 120 months later: August 1936 for the market, SMB and HML, January 1937 for momentum, August 1973 for RMW and CMA.
"""),
    md("""
## How this notebook is organised

1. The modules are written into the runtime and the series are built.
2. Table 1: the original and the volatility-managed factors beside the published numbers.
3. Table 5: S1, S2 and S3 beside the published numbers.
4. One Jobson-Korkie test worked from monthly numbers: momentum's S1 against S2.
5. E2 judged: the twenty-four comparisons and the verdict.
6. The cause of the result, and two diagnostics computed after it.
7. The outputs, the summary and what could be wrong.
"""),
    SETUP,
    writefile("constants.py"),
    writefile("published.py"),
    writefile("french_loader.py"),
    writefile("managed.py"),
    writefile("regression.py"),
    writefile("verdicts.py"),
    writefile("diagnostics.py"),
    code("""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from sq import constants as C, published as P, french_loader as fl, managed as M, regression as R, verdicts as V
from sq import diagnostics as D

records = [fl.download(key) for key in C.FRENCH_FILES]
fl.write_provenance(records)
VINTAGE = sorted({r["vintage_line"].split("the ")[-1].split(" ")[0] for r in records})[-1]
print("vintage:", VINTAGE)
monthly = fl.factors("monthly")
daily = fl.factors("daily")
pd.set_option("display.width", 200)


def build(f, rv, first):
    \"\"\"The series of Tables 1 and 5 for one factor on Cederburg et al.'s sample.\"\"\"
    vm, _ = M.volatility_managed(f, rv, first, C.COWY_SAMPLE_END)          # Table 1
    rt = M.real_time(f, rv, first, C.COWY_SAMPLE_END)                     # S1 and S2
    oos, _ = M.volatility_managed(f, rv, str(rt.index[0]), C.COWY_SAMPLE_END)
    s3, w = M.ex_post_combination(oos["managed"], oos["f"])                # S3, on the out-of-sample months
    return {"vm": vm, "rt": rt, "s3": s3, "w3": w}


def comparisons(b):
    \"\"\"The Sharpe ratios E2 reads, with the Jobson-Korkie tests of the two differences.\"\"\"
    rt = b["rt"]
    d12 = R.jobson_korkie(rt["s1"], rt["s2"])
    d13 = R.jobson_korkie(rt["s1"], b["s3"].loc[rt.index])
    return {"sharpe_original": R.sharpe(b["vm"]["f"]), "sharpe_managed": R.sharpe(b["vm"]["managed"]),
            "s1": R.sharpe(rt["s1"]), "s2": R.sharpe(rt["s2"]), "s1_minus_s2": d12["difference"], "p_s1_s2": d12["p"],
            "s3": R.sharpe(b["s3"]), "s1_minus_s3": d13["difference"], "p_s1_s3": d13["p"]}


rv = {f: M.rv_cowy(daily[f].dropna()) for f in C.FACTORS}                # Cederburg et al.'s definition, equation 4
built = {f: build(monthly[f], rv[f], C.FACTOR_FIRST_MONTH[f]) for f in C.FACTORS}
print(pd.DataFrame({f: {"Table 1 months": len(b["vm"]), "published": C.COWY_EXPECTED_N[f],
                        "first out-of-sample month": str(b["rt"].index[0]), "out-of-sample months": len(b["rt"])}
                    for f, b in built.items()}).to_string())
"""),
    md("""
## 2. Table 1: the original and the volatility-managed factors

Mean and standard deviation in per cent a year, Sharpe ratio annualised, each factor over its own months to December 2016. The managed factor's standard deviation equals the original's by the choice of c. The last two rows are Table 1, Panel C: the difference of the two Sharpe ratios and its Jobson-Korkie p-value.
"""),
    code("""
rows = {}
for f, b in built.items():
    o, m = b["vm"]["f"], b["vm"]["managed"]
    jk = R.jobson_korkie(m, o)
    po, pm, pc = P.COWY_TABLE_1_ORIGINAL[f], P.COWY_TABLE_1_MANAGED[f], P.COWY_TABLE_1_DIFFERENCE[f]
    rows[f] = {
        "original mean, published": po[0], "original mean, computed": o.mean() * 1200,
        "original sd, published": po[1], "original sd, computed": o.std() * np.sqrt(12) * 100,
        "original Sharpe, published": po[2], "original Sharpe, computed": R.sharpe(o),
        "managed mean, published": pm[0], "managed mean, computed": m.mean() * 1200,
        "managed Sharpe, published": pm[2], "managed Sharpe, computed": R.sharpe(m),
        "difference, published": pc[0], "difference, computed": jk["difference"],
        "p, published": pc[1], "p, computed": jk["p"],
    }
table_1 = pd.DataFrame(rows)
print(table_1.round(3).to_string())
"""),
    md("""
## 3. Table 5: the real-time and the ex post strategies

Sharpe ratios over each factor's out-of-sample period, the differences with their Jobson-Korkie p-values, the share of months in which S1's and S2's positions sit at the cap, and S3's two weights: on the volatility-managed factor, scaled to the original's standard deviation over the out-of-sample months, and on the original factor.
"""),
    code("""
computed = pd.DataFrame({f: comparisons(b) for f, b in built.items()}).T
rows = {}
for f, b in built.items():
    s1_p, s2_p, d12_p, s3_p, d13_p = P.COWY_TABLE_5[f]
    p12_p, p13_p = P.COWY_TABLE_5_P[f]
    c = computed.loc[f]
    rt = b["rt"]
    rows[f] = {
        "S1, published": s1_p, "S1, computed": c["s1"], "S2, published": s2_p, "S2, computed": c["s2"],
        "S1-S2, published": d12_p, "S1-S2, computed": c["s1_minus_s2"], "p, published": p12_p, "p, computed": c["p_s1_s2"],
        "S3, published": s3_p, "S3, computed": c["s3"],
        "S1-S3, published": d13_p, "S1-S3, computed": c["s1_minus_s3"], "p S1-S3, published": p13_p, "p S1-S3, computed": c["p_s1_s3"],
        "S1 months at the cap": rt["at_cap"].mean(), "S2 months at the cap": (rt["y2"].abs() >= C.REALTIME_LEVERAGE_CAP).mean(),
        "S3 weight, volatility-managed": b["w3"][0], "S3 weight, original": b["w3"][1],
    }
table_5 = pd.DataFrame(rows)
print(table_5.round(3).to_string())
"""),
    md("""
## 4. One test worked: momentum's S1 against S2

The Jobson-Korkie statistic compares the two Sharpe ratios through the monthly means m, standard deviations s and the covariance s_12 of the two return series over the same T months (Cederburg et al., p. 99):

z = (s_2 m_1 - s_1 m_2) / sqrt(theta), with theta = (1/T) (2 s_1² s_2² - 2 s_1 s_2 s_12 + m_1² s_2² / 2 + m_2² s_1² / 2 - (m_1 m_2 / (s_1 s_2)) s_12²).

The p-value is the probability that a standard normal variable lies further from 0 than z.
"""),
    code("""
from statistics import NormalDist
rt = built["Mom"]["rt"]
a, b2 = rt["s1"].to_numpy(), rt["s2"].to_numpy()
T = len(a)
m1, m2, s1, s2 = a.mean(), b2.mean(), a.std(ddof=1), b2.std(ddof=1)
s12 = np.cov(a, b2)[0, 1]
theta = (2 * s1**2 * s2**2 - 2 * s1 * s2 * s12 + m1**2 * s2**2 / 2 + m2**2 * s1**2 / 2 - m1 * m2 / (s1 * s2) * s12**2) / T
z = (s2 * m1 - s1 * m2) / np.sqrt(theta)
print(f"T = {T} months; S1 monthly mean {m1:.5f}, sd {s1:.5f}; S2 monthly mean {m2:.5f}, sd {s2:.5f}; covariance {s12:.6f}")
print(f"Sharpe ratios, annualised: S1 {m1 / s1 * np.sqrt(12):.3f}, S2 {m2 / s2 * np.sqrt(12):.3f}")
print(f"theta = {theta:.3e}; z = {z:.2f}; p = {2 * (1 - NormalDist().cdf(abs(z))):.5f}")
"""),
    md("""
## 5. E2 judged

One row per factor, the four comparisons of E2 beside the published numbers, then the verdict with the arithmetic beside each clause.
"""),
    code("""
e2_table, e2_clauses, e2_met = V.e2(computed)
print(e2_table.T.to_string())
print()
e2_text = V.e2_line(e2_table, e2_clauses)
print(e2_text)
"""),
    md("""
## 6. The cause of the result, and two diagnostics

The verdict above stands as printed. This section reads its cause and judges nothing.

**The original factors.** Each original factor's mean and standard deviation over its own Table 1 months, beside Table 1's, and the Sharpe ratio each pair gives. For RMW those months are the 641 from August 1963 to December 2016.
"""),
    code("""
rows = {}
for f, b in built.items():
    o = b["vm"]["f"]
    mean_p, sd_p, _ = P.COWY_TABLE_1_ORIGINAL[f]
    rows[f] = {"months": len(o), "mean, published": mean_p, "mean, computed": o.mean() * 1200,
               "sd, published": sd_p, "sd, computed": o.std() * np.sqrt(12) * 100,
               "Sharpe from Table 1's mean and sd": mean_p / sd_p, "Sharpe, computed": R.sharpe(o)}
cause = pd.DataFrame(rows).T
cause["Sharpe, computed minus published"] = cause["Sharpe, computed"] - cause["Sharpe from Table 1's mean and sd"]
print(cause.round(3).to_string())
"""),
    md("""
On vintage 202609, five of the original factors lie within 0.01 of the Sharpe ratio Table 1's mean and standard deviation give. RMW's lies 0.027 above, with the same standard deviation: its mean is 3.12 per cent a year against Table 1's 2.92. The original factor's mean depends on no choice of signal or construction; it is French's series as downloaded. French's library revises its series: each new file is rebuilt from the current release of the underlying data, and the history of a factor can change with it. RMW is sorted on firms' accounting data as well as on their returns. The one direct test, French's RMW file as Cederburg et al. downloaded it, is not in the design's data.

The design allowed two diagnostics after the result. Each is computed after the verdict and carries none.

**Diagnostic (a): RMW with its mean moved to Table 1's.** RMW's monthly returns are moved by one constant so that their mean over the 641 months equals Table 1's 2.92 per cent a year. The daily returns, and so the signal, are left as they are. The four RMW comparisons are rebuilt from the moved series. The part of the miss the shift closes is the part the mean alone accounts for; the part that remains comes from the revision's change to individual months.
"""),
    code("""
first, end = C.FACTOR_FIRST_MONTH["RMW"], C.COWY_SAMPLE_END
shifted, delta = D.shift_to_mean(monthly["RMW"], first, end, P.COWY_TABLE_1_ORIGINAL["RMW"][0])
print(f"the constant: {delta * 1200:.3f} per cent a year ({delta:.6f} a month)")
moved = comparisons(build(shifted, rv["RMW"], first))
s1_p, s2_p, d12_p, s3_p, d13_p = P.COWY_TABLE_5["RMW"]
diag_a = pd.DataFrame({
    "published": {"original Sharpe": P.COWY_TABLE_1_ORIGINAL["RMW"][2], "managed Sharpe": P.COWY_TABLE_1_MANAGED["RMW"][2],
                  "S1": s1_p, "S2": s2_p, "S1-S2": d12_p, "p S1-S2": P.COWY_TABLE_5_P["RMW"][0], "S1-S3": d13_p},
    "computed": {"original Sharpe": computed.loc["RMW", "sharpe_original"], "managed Sharpe": computed.loc["RMW", "sharpe_managed"],
                 "S1": computed.loc["RMW", "s1"], "S2": computed.loc["RMW", "s2"], "S1-S2": computed.loc["RMW", "s1_minus_s2"],
                 "p S1-S2": computed.loc["RMW", "p_s1_s2"], "S1-S3": computed.loc["RMW", "s1_minus_s3"]},
    "computed, mean moved": {"original Sharpe": moved["sharpe_original"], "managed Sharpe": moved["sharpe_managed"],
                             "S1": moved["s1"], "S2": moved["s2"], "S1-S2": moved["s1_minus_s2"],
                             "p S1-S2": moved["p_s1_s2"], "S1-S3": moved["s1_minus_s3"]},
})
diag_a["gap, computed"] = (diag_a["computed"] - diag_a["published"]).abs()
diag_a["gap, mean moved"] = (diag_a["computed, mean moved"] - diag_a["published"]).abs()
print(diag_a.round(3).to_string())
"""),
    md("""
**Diagnostic (b): RMW in the Internet Archive's copy of French's file.** The Internet Archive holds one copy of French's five-factor file from 2017 and 2018, captured on 9 July 2017 at https://web.archive.org/web/20170709190513/http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip. Its first line names the release it was built from. The code fetches it into `data/archive/`, which is never committed, checks its SHA-256 against the value read when the copy was found, and reads the original RMW's mean and standard deviation over the same 641 months, beside Table 1's and vintage 202609's. If the archive cannot be reached, the cell says so and the notebook goes on.
"""),
    code("""
archived, record = D.archived_five_factor()
for k, v in record.items():
    print(f"{k}: {v}")
if archived is None:
    print("The Internet Archive could not be reached in this run; diagnostic (b) has no number.")
    diag_b = pd.DataFrame()
else:
    diag_b = pd.DataFrame({
        "Table 1 (published)": {"months": C.COWY_EXPECTED_N["RMW"], "mean": P.COWY_TABLE_1_ORIGINAL["RMW"][0], "sd": P.COWY_TABLE_1_ORIGINAL["RMW"][1]},
        f"archived copy, {D.ARCHIVE_DATE}": D.moments(archived["RMW"], first, end),
        f"vintage {VINTAGE}": D.moments(monthly["RMW"], first, end),
    }).T[["months", "mean", "sd"]]
    print(diag_b.round(3).to_string())
"""),
    md("""
## 7. The outputs, the summary, and what could be wrong

Tables 1 and 5 as computed, the E2 comparison and verdict, the cause and the two diagnostics go to `outputs/` with the vintage in each name.
"""),
    code("""
table_1.T.to_csv(f"outputs/cowy_table_1_computed_{VINTAGE}.csv")
table_5.T.to_csv(f"outputs/cowy_table_5_computed_{VINTAGE}.csv")
e2_table.to_csv(f"outputs/e2_comparison_{VINTAGE}.csv")
pd.DataFrame([{"expectation": "E2", "comparisons holding": int(e2_table["comparisons holding"].sum()), "comparisons": 4 * len(e2_table),
               **{f"clause {k}": "met" if v else "not met" for k, v in e2_clauses.items()},
               "verdict": "met" if e2_met else "not met", "vintage": VINTAGE}]).to_csv(f"outputs/e2_verdict_{VINTAGE}.csv", index=False)
cause.to_csv(f"outputs/e2_cause_original_factors_{VINTAGE}.csv")
diag_a.to_csv(f"outputs/e2_diagnostic_a_rmw_mean_moved_{VINTAGE}.csv")
if not diag_b.empty:
    diag_b.to_csv(f"outputs/e2_diagnostic_b_rmw_archived_{VINTAGE}.csv")

summary = pd.DataFrame([{
    "expectation": "E2: Cederburg et al.'s Tables 1 and 5 on their sample",
    "result": e2_text.splitlines()[0][len("E2: "):] + " " + " ".join(
        f"{k} {'met' if v else 'not met'}." for k, v in e2_clauses.items()),
    "verdict": "met" if e2_met else "not met",
}]).set_index("expectation")
print(summary.to_string())
print(sorted(os.listdir("outputs")))
"""),
    md("""
What could be wrong, and where each point is tested:

- **French's data have been revised since the paper.** Section 6 reads the size of the revision for every original factor and, for RMW, from an archived copy of the file.
- **The cap.** Cederburg et al. state the limit on the position two ways: a position of at most 5 in either direction in the text (p. 107), and a sum of absolute weights on the factors of at most 5 in the note to Table 5 (p. 106). The module applies the text's version and truncates the position at 5; section 3 prints the share of months in which it binds. S3's two weights, with the volatility-managed factor scaled to the original's standard deviation over the out-of-sample months, sum to less than 5 in absolute value for every factor (section 3 prints them), so the note's version does not bind for S3, and the module applies no cap to it.
- **The test.** The p-values rest on the Jobson-Korkie normal approximation, the one Cederburg et al. use, so the computed and the published p-values are compared on the same test. Notebook 06 tests Sharpe ratio differences with Ledoit and Wolf's bootstrap, which does not rest on that approximation.
- **S3 uses the months it is judged on.** S1 minus S3 measures what estimating the weights in real time costs; it is a property of these months and of the training period's length, 120 months.
"""),
]


# ---------------------------------------------------------------------------
# 05: Barroso and Santa-Clara's scaled momentum (E3)
# ---------------------------------------------------------------------------

NB05 = [
    md("""
# 05. Barroso and Santa-Clara's scaled momentum on their sample, and to August 2026 (E3)

**Terms used in this notebook.**

| Term | Meaning |
|---|---|
| Factor | the monthly return of one long-short portfolio that captures one source of common movement in stock returns; Moreira and Muir's six are Mkt-RF, SMB, HML, Mom, RMW and CMA |
| Momentum | the tendency of stocks that rose most over the past year to keep rising, and of those that fell most to keep falling, over the next months |
| Decile | one tenth of the stocks, ranked by a characteristic. French's ten momentum portfolios rank stocks by their return from twelve months to two months before the portfolio is formed |
| Value-weighted return | the return of a group of firms in which each firm counts in proportion to its market value at the start of the period |
| WML | winners minus losers: the top momentum decile's value-weighted return minus the bottom decile's (Barroso and Santa-Clara, Appendix A, p. 119). A long-short position, paid for by its own short side |
| Trading day | a day on which the New York Stock Exchange traded, one row of French's daily files |
| Realised variance | here Barroso and Santa-Clara's (equation 5, p. 115): 21 times the mean squared daily return of WML over the last 126 trading days, measured at the last trading day of the month, a monthly variance |
| Volatility | the square root of a variance: the typical size of a return's swing |
| Target volatility | the volatility the scaled series aims at: 12 per cent a year (p. 115), 3.46 per cent a month |
| Weight | the multiple of WML held in a month: the target volatility divided by last month's volatility |
| Scaled WML | WML times the weight (equation 6, p. 115): a position that shrinks after volatile months and grows after calm ones |
| Sharpe ratio | the average return divided by its standard deviation, annualised: times the square root of 12 |
| Compounding | growing wealth month by month by (1 + the month's return), so that each month's return applies to the wealth left by the months before |
| Maximum drawdown | the largest fall of compounded wealth from its highest earlier level, in per cent |
| Excess kurtosis | a measure of how often returns land far from their mean, relative to the normal distribution, which has 0 |
| Skewness | a measure of the asymmetry of returns; negative when the large moves are mostly falls |
| Verdict | met or not met: the result of an expectation, read from levels fixed before the code ran |
| Vintage | the version of French's files on the download date, named by the CRSP release they were built from |

**What this notebook does.** It builds WML from French's ten momentum portfolios, monthly and daily, computes Barroso and Santa-Clara's realised variance from the daily series, and scales WML to a 12 per cent target volatility. On their sample it puts every number of their Table 3 (p. 116) and the two maximum drawdowns (p. 112) beside the computed ones and judges E3. It then reports the same two series to August 2026, which no expectation judges.

**Why it comes at this point.** Barroso and Santa-Clara scale momentum by its own recent volatility, the same idea as Moreira and Muir's, built with information available at the time: the target is fixed in advance and the weight uses only the months before. It is the study's one robustness check of the signal on a different series and a different definition of the variance.

**The expectation it judges: E3**, fixed in `src/sq/constants.py` before this notebook's code was written. On May 1927 to December 2011:

1. the Sharpe ratios of unscaled and scaled WML lie within 0.05 of 0.53 and 0.97 (Table 3, p. 116);
2. the maximum drawdowns lie within five percentage points of 96.69 and 45.20 per cent (p. 112).

E3 is met when all four comparisons hold. The first scaled month is May 1927, two months after the paper's March 1927, because French's daily file of the ten momentum portfolios starts on 3 November 1926 and the variance needs 126 trading days.

**Why these levels.** The paper's two headline results, on its own momentum series (Appendix A, p. 119). The margin of 0.05 on a Sharpe ratio is the one used throughout the study; five points on a drawdown is a margin of the same order on a number measured in per cent.

**What I expect to see, and where it comes from.** E3 met. Table 3 of the paper, 1927:03 to 2011:12, monthly returns in per cent for the maximum and the minimum, mean and standard deviation in per cent a year:

| | Maximum | Minimum | Mean | Standard deviation | Excess kurtosis | Skewness | Sharpe ratio |
|---|---|---|---|---|---|---|---|
| WML | 26.18 | -78.96 | 14.46 | 27.53 | 18.24 | -2.47 | 0.53 |
| scaled WML | 21.95 | -28.40 | 16.50 | 16.95 | 2.68 | -0.42 | 0.97 |

The maximum drawdown is 96.69 per cent for WML and 45.20 per cent for scaled WML (p. 112). Two crashes the paper states (p. 113): WML's compounded return over July and August 1932 is -91.59 per cent, and over March to May 2009 -73.42 per cent. The weight ranges from 0.13 to 2.00 and averages 0.90 (p. 116). The paper's momentum series comes from a different source than French's portfolios (Appendix A), so the unjudged numbers can differ by more than the judged ones.
"""),
    md("""
## How this notebook is organised

1. The modules are written into the runtime and WML is built, monthly and daily.
2. The first scaled month worked by hand, and the two crashes compounded.
3. Table 3 and the weight beside the published numbers.
4. E3 judged.
5. The same two series to August 2026, which no expectation judges.
6. The outputs, the summary and what could be wrong.
"""),
    SETUP,
    writefile("constants.py"),
    writefile("published.py"),
    writefile("french_loader.py"),
    writefile("managed.py"),
    writefile("regression.py"),
    writefile("verdicts.py"),
    code("""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from sq import constants as C, published as P, french_loader as fl, managed as M, regression as R, verdicts as V

records = [fl.download(key) for key in C.FRENCH_FILES]
fl.write_provenance(records)
VINTAGE = sorted({r["vintage_line"].split("the ")[-1].split(" ")[0] for r in records})[-1]
print("vintage:", VINTAGE)
pd.set_option("display.width", 200)

wml = fl.wml("monthly")
wml_daily = fl.wml("daily")
rv = M.rv_bsc(wml_daily)                                  # Barroso and Santa-Clara's definition, equation 5
bsc = M.scaled_momentum(wml, rv, C.BSC_FIRST_MONTH, C.BSC_SAMPLE_END)
ext = M.scaled_momentum(wml, rv, C.BSC_FIRST_MONTH, C.BSC_EXTENDED_END)
print("first daily row:", wml_daily.index[0], "; first month with 126 trading days:", rv.dropna().index[0])
print("the paper's sample:", bsc.index[0], "to", bsc.index[-1], len(bsc), "months; expected", C.BSC_EXPECTED_MONTHS)
print("to the sample end:", ext.index[0], "to", ext.index[-1], len(ext), "months")
"""),
    md("""
## 2. The first scaled month, and the two crashes

May 1927's weight comes from the 126 trading days that end on April 1927's last trading day: their mean squared return times 21 is a monthly variance, its square root a monthly volatility, and the weight is the target, 0.12 divided by the square root of 12, over that volatility.
"""),
    code("""
last_126 = wml_daily.loc[:"1927-04-30"].iloc[-126:]
var_month = 21 * (last_126 ** 2).mean()
sigma = np.sqrt(var_month)
print(f"126 trading days from {last_126.index[0]} to {last_126.index[-1]}")
print(f"monthly variance {var_month:.6f}; monthly volatility {sigma:.4f}, {sigma * np.sqrt(12):.1%} a year")
print(f"weight for May 1927: {C.BSC_TARGET_VOL_MONTHLY:.4f} / {sigma:.4f} = {C.BSC_TARGET_VOL_MONTHLY / sigma:.3f}; the module: {bsc['weight'].iloc[0]:.3f}")
print(f"May 1927: WML {bsc['wml'].iloc[0]:.4f}, scaled {bsc['scaled'].iloc[0]:.4f}")
print()
for a, b, pub in (("1932-07", "1932-08", -91.59), ("2009-03", "2009-05", -73.42)):
    print(f"WML compounded {a} to {b}: {((1 + wml.loc[a:b]).prod() - 1):.2%}; the paper (p. 113): {pub} per cent")
"""),
    md("""
## 3. Table 3 and the weight

Maximum and minimum monthly returns in per cent, mean and standard deviation in per cent a year, excess kurtosis and skewness of the monthly returns, Sharpe ratio annualised, on May 1927 to December 2011. The weight's range and average beside the paper's. None of these is judged except the Sharpe ratio, in section 4.
"""),
    code("""
def describe(r):
    return {"maximum": r.max() * 100, "minimum": r.min() * 100, "mean": r.mean() * 1200, "standard deviation": r.std() * np.sqrt(12) * 100,
            "excess kurtosis": r.kurt(), "skewness": r.skew(), "Sharpe ratio": R.sharpe(r)}

fields = ["maximum", "minimum", "mean", "standard deviation", "excess kurtosis", "skewness", "Sharpe ratio"]
pub = {"WML": dict(zip(fields, (P.BSC_TABLE_3_WML[i] for i in (0, 1, 2, 3, 4, 5, 6)))),
       "scaled WML": dict(zip(fields, (P.BSC_TABLE_3_WML_SCALED[i] for i in (0, 1, 2, 3, 4, 5, 6))))}
table_3 = pd.DataFrame({
    "WML, published": pub["WML"], "WML, computed": describe(bsc["wml"]),
    "scaled WML, published": pub["scaled WML"], "scaled WML, computed": describe(bsc["scaled"]),
})
print(table_3.round(3).to_string())
print()
print(f"weight: minimum {bsc['weight'].min():.2f}, maximum {bsc['weight'].max():.2f}, average {bsc['weight'].mean():.2f}; the paper: 0.13, 2.00, 0.90")
"""),
    md("""
## 4. E3 judged
"""),
    code("""
computed = {"sharpe_wml": R.sharpe(bsc["wml"]), "sharpe_scaled": R.sharpe(bsc["scaled"]),
            "mdd_wml": R.max_drawdown(bsc["wml"]), "mdd_scaled": R.max_drawdown(bsc["scaled"])}
e3_table, e3_met = V.e3(computed)
print(e3_table.T.to_string())
print()
e3_text = V.e3_line(e3_table, e3_met)
print(e3_text)
"""),
    md("""
## 5. To August 2026

The same two series on May 1927 to August 2026, the study's sample end. No expectation judges these numbers; they are the second period of the specification the design lists for scaled momentum.
"""),
    code("""
extended = pd.DataFrame({
    "WML": {"months": len(ext), "mean": ext["wml"].mean() * 1200, "standard deviation": ext["wml"].std() * np.sqrt(12) * 100,
            "Sharpe ratio": R.sharpe(ext["wml"]), "maximum drawdown (%)": R.max_drawdown(ext["wml"]) * 100},
    "scaled WML": {"months": len(ext), "mean": ext["scaled"].mean() * 1200, "standard deviation": ext["scaled"].std() * np.sqrt(12) * 100,
                   "Sharpe ratio": R.sharpe(ext["scaled"]), "maximum drawdown (%)": R.max_drawdown(ext["scaled"]) * 100},
})
print(extended.round(3).to_string())
"""),
    md("""
## 6. The outputs, the summary, and what could be wrong

Table 3 as computed, the E3 comparison and verdict, the period to August 2026 and the monthly series go to `outputs/` with the vintage in each name.
"""),
    code("""
table_3.to_csv(f"outputs/bsc_table_3_computed_{VINTAGE}.csv")
e3_table.to_csv(f"outputs/e3_comparison_{VINTAGE}.csv")
pd.DataFrame([{"expectation": "E3", "comparisons holding": int(e3_table["Sharpe within 0.05"].sum() + e3_table["drawdown within five points"].sum()),
               "comparisons": 4, "verdict": "met" if e3_met else "not met", "vintage": VINTAGE}]).to_csv(f"outputs/e3_verdict_{VINTAGE}.csv", index=False)
extended.to_csv(f"outputs/scaled_wml_to_sample_end_{VINTAGE}.csv")
ext.to_csv(f"outputs/scaled_wml_series_{VINTAGE}.csv")

summary = pd.DataFrame([{
    "expectation": "E3: Barroso and Santa-Clara's scaled momentum on May 1927 to December 2011",
    "result": e3_text.split(". ", 1)[1],
    "verdict": "met" if e3_met else "not met",
}]).set_index("expectation")
print(summary.to_string())
print(sorted(os.listdir("outputs")))
"""),
    md("""
What could be wrong, and where each point is tested:

- **The series.** The paper's WML comes from Daniel and Moskowitz's data, French's from his own portfolios (Appendix A). The two crashes of section 2, compounded from French's series, are set beside the paper's figures as a check of the series and of the compounding.
- **The start.** French's daily file starts on 3 November 1926, so the first scaled month is May 1927 and both series miss the paper's March and April 1927: 2 of the paper's 1,018 months. Section 4 judges the 1,016 that remain.
- **The variance.** Equation 5 averages 126 squared daily returns without removing their mean and multiplies the average by 21, a month of trading days; the module follows the equation as printed. Section 2 works one month of it by hand.
- **The months after 2011.** Section 5 reports them and judges nothing. The study tests a gain after a paper's sample on Moreira and Muir's six factors only (E5, notebook 07), and states no test for scaled momentum after 2011.
"""),
]


NOTEBOOKS = {
    "01": ("01_french_loader.ipynb", NB01),
    "02": ("02_realised_variance.ipynb", NB02),
    "03": ("03_moreira_muir.ipynb", NB03),
    "04": ("04_cederburg_et_al.ipynb", NB04),
    "05": ("05_barroso_santa_clara.ipynb", NB05),
}


if __name__ == "__main__":
    # With numbers ("python3 build_notebooks.py 03 04") only those notebooks are written: a notebook run and
    # committed at an earlier milestone keeps the module code it ran with, and is rebuilt only when its own
    # content changes. With no numbers every notebook is written.
    import sys
    for key in (sys.argv[1:] or list(NOTEBOOKS)):
        name, cells = NOTEBOOKS[key]
        print(write(name, cells))
