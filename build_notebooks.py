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


if __name__ == "__main__":
    for name, cells in (("01_french_loader.ipynb", NB01),):
        print(write(name, cells))
