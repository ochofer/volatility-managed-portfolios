# Volatility-managed portfolios: a replication, the real-time critique, and the months after the sample

Moreira and Muir (2017) scale a factor's position each month by the inverse of its realised variance in the month before, and find positive alphas against the unscaled factor. Cederburg, O'Doherty, Wang and Yan (2020) estimate in real time how an investor would combine the scaled and the original factor, and find, for the six factors studied here, little gain outside momentum. This repository replicates both papers and the scaled momentum of Barroso and Santa-Clara (2015) on Ken French's six factors, tests the Sharpe ratio differences with the bootstrap of Ledoit and Wolf (2008), and measures what the signal did in the 136 months after Moreira and Muir's sample, May 2015 to August 2026.

The results are on the [dashboard](https://www.carlohofer.com/volatility-managed-portfolios/dashboard/B-Q_dashboard.html) and in the [note](https://www.carlohofer.com/volatility-managed-portfolios/note/B-Q_note_2026-11.pdf). The project page is [carlohofer.com/projects/volatility-managed-portfolios](https://www.carlohofer.com/projects/volatility-managed-portfolios/).

## Findings

The study has three parts, the *replications*, the *two tests* on Moreira and Muir's sample and the *months after the sample*.

- **The replications.** Moreira and Muir's Table I reproduces for 6 of 6 factors: the market's alpha is 4.93 per cent a year with a White standard error of 1.57, against the paper's 4.86 and 1.56. Barroso and Santa-Clara's scaled momentum reproduces in 4 of 4 comparisons, with a Sharpe ratio of 1.00 against the paper's 0.97. Cederburg et al.'s results reproduce in 22 of 24 comparisons, and both misses are on RMW, whose mean in French's current file is 3.12 per cent a year on their months against their 2.92, i.e., French has most likely revised the factor since.
- **The two tests.** The alphas of the market, momentum and RMW are statistically significant at the 5 per cent level on their Newey-West t-statistics after Holm's correction for the six tests. Held in the original's place, the scaled factor's Sharpe ratio is higher by a margin that is statistically significant at that level for momentum alone, tested on its own, +0.51 annualised (0.07 to 0.96), and for no factor after the correction. The two tests differ because the alpha measures what the scaled factor adds to a holding of the original, and the Sharpe ratio difference measures the scaled factor held in the original's place.
- **The months after the sample.** None of the twelve Sharpe ratio differences, i.e., the real-time combination against the real-time original and the scaled factor against the original, for each of the six factors, is statistically significant at the 5 per cent level, and for the six volatility-managed factors the intervals are too wide to rule out the differences found on Moreira and Muir's sample. At 136 months the test rejects 2.0 per cent of simulated pairs with equal Sharpe ratios (1.3 to 3.1) where 5 is intended, so these months are weak evidence either way.
- **Costs.** At 10 basis points per unit of turnover the market's alpha is 4.03 per cent a year (t 2.31), statistically significant at the 5 per cent level, and at 20 basis points 3.13 (t 1.81), which is not.

Of the six expectations, four are met and two are not: E2, the real-time critique, because of RMW, and E4, which expected the two tests to agree for at least five factors where they agree for two.

## The note and the dashboard

`note/B-Q_note_2026-11.pdf`, with its HTML source beside it, gives the study in full: the three replications beside the published figures, RMW's revision, the two tests and the identity that links them, the months after the sample, the costs and positions, and the limits of the design. `dashboard/B-Q_dashboard.html` shows the results in five views, *Summary*, *Replication*, *In the sample*, *After the sample* and *Method and terms*. The last lists the committed table each exhibit is drawn from. The dashboard is built by `python3 dashboard/build_dashboard.py` from the committed tables alone, run from the repository root.

## How to run

Each notebook runs from a blank Google Colab runtime: upload it and run all cells. It writes the code it needs into `src/sq/` and downloads French's files at run time, so none of them is stored here. From a checkout, run `pip install -r requirements.txt`, then `python3 -m pytest tests`, then the notebooks in order. `build_notebooks.py` writes the notebooks from their text and the modules in `src/sq/`, and they are committed without outputs.

Each notebook writes its tables to `outputs/` with a record of each file's download date, hash and vintage. The tables the note and the dashboard cite are committed in `results/202609/`, computed on the files French built from the CRSP database of September 2026. The sample ends in August 2026 whatever the vintage. French revises his files, so a run on a later vintage reproduces the verdicts and not every digit.

## What is fixed in advance

Every sample boundary, construction setting and expectation is in `src/sq/constants.py`, each with its source, and the published figures the replications are compared with are in `src/sq/published.py`, each with its page and table. Each notebook opens with the expectations it tests, written before its code ran, and marks the comparisons added after the results were known.

## The notebooks

| Notebook | What it does |
|---|---|
| 01 `french_loader` | Reads French's daily and monthly files, the six factors and WML, and records the vintage |
| 02 `realised_variance` | Builds the signal under each paper's definition, the volatility-managed factor, the real-time combination and their positions |
| 03 `moreira_muir` | Moreira and Muir's Table I on their sample (E1) |
| 04 `cederburg_et_al` | Cederburg et al.'s Tables 1 and 5 on their sample, with RMW's revision (E2) |
| 05 `barroso_santa_clara` | Scaled momentum on Barroso and Santa-Clara's sample and to August 2026 (E3) |
| 06 `sharpe_test` | Ledoit and Wolf's test, its size on simulated pairs, the six factors on Moreira and Muir's sample, and the identity that links the two tests (E4) |
| 07 `after_the_sample` | May 2015 to August 2026, both constructions carried forward (E5) |
| 08 `costs` | Turnover, the alpha net of 10 and 20 basis points, the break-even cost and the size of the positions (E6) |

## Terms

- **Volatility-managed factor**: the factor's return times a constant c over last month's realised variance, c giving it the original's standard deviation over the whole sample.
- **Realised variance**: the variance of a factor computed from its daily returns within one month, each paper with its own definition, given in `src/sq/constants.py`.
- **Real-time combination (S1)**: a mix of the volatility-managed and the original factor whose weights are estimated each month from the months before it. The **real-time original (S2)** is the original factor alone at its real-time weight.
- **Scaled momentum**: WML, i.e., the top momentum decile's return minus the bottom decile's, held at 12 per cent a year over its realised volatility of the previous 126 trading days.
- **Alpha**: the intercept of the regression of a volatility-managed factor on its original, in per cent a year.
- **Interval**: the 95 per cent interval of Ledoit and Wolf's test for the true Sharpe ratio difference. A difference is statistically significant at the 5 per cent level when its interval excludes zero.
- **Holm's correction**: for n tests read together, the smallest p-value is multiplied by n, the next by n − 1 and so on, each kept at least as large as the one before and none above one.
- **Turnover**: the absolute change in the position from one month to the next.
- **Vintage**: the version of French's files, named by the CRSP database they were built from.

## Layout

```
build_notebooks.py       writes notebooks/ from their text and the code in src/sq/
src/sq/constants.py      every sample boundary, setting and expectation, with its source
src/sq/published.py      the published figures of the three papers, with page and table
src/sq/french_loader.py  the download, provenance and parsing of French's files
src/sq/managed.py        the signal, the volatility-managed factor, the real-time and ex post combinations, scaled momentum and the cost of turnover
src/sq/regression.py     the regression of a volatility-managed factor on its original, its standard errors and the Sharpe ratios
src/sq/bootstrap.py      Ledoit and Wolf's test of a Sharpe ratio difference
src/sq/verdicts.py       each expectation judged from the computed and the published figures
src/sq/diagnostics.py    the checks on RMW's revision, outside the verdicts
notebooks/               the eight notebooks, run in order
dashboard/               the dashboard, its template, its chart script and its build
note/                    the note, as HTML and as PDF
outputs/                 written at run time and not committed
results/202609/          the tables the note and the dashboard cite, with the provenance record
tests/                   checks that run without network
```

## Other projects

**Optimal versus naive diversification.** Under a long-only index-tracking mandate on French's 49 industries, 1979 to 2026, each of five covariance estimators forecasts less tracking error than its portfolio realises: the realised active return is 22 to 61 per cent more volatile than forecast. The replication of DeMiguel, Garlappi and Uppal (2009) reproduces 29 of the 30 out-of-sample Sharpe ratios within 0.03 of the published values. [Page](https://www.carlohofer.com/projects/optimal-vs-naive-diversification/), [dashboard](https://www.carlohofer.com/optimal-vs-naive-diversification/dashboard/B-P_dashboard.html), [note](https://www.carlohofer.com/optimal-vs-naive-diversification/note/B-P_note_2026-10.pdf), [code](https://github.com/ochofer/optimal-vs-naive-diversification)

**Climate risk as an equity signal.** An ownership graph linking 328 ownership entities in the US and developed Europe, 302 of them listed companies with a price series, to 5,115 asset holdings, built from Global Energy Monitor's free tracker. Of 19 apparent ownership changes drawn at random and checked by hand, 12 had no corporate event behind them. [Page](https://www.carlohofer.com/projects/climate-risk-equity-signal/), [note](https://github.com/ochofer/paper1-hazard-exposure-data/releases/download/note-v1.3/what-a-vintage-difference-measures.pdf), [code](https://github.com/ochofer/paper1-hazard-exposure-data)

**Stock-level index tracking: a point-in-time benchmark, a long-only mandate, and its performance attribution by sector.** Rebuilds the S&P 500 month by month from CRSP's list of members, at a tracking error of 11.5 basis points a year against CRSP's own return of the same list, and runs a long-only index-tracking mandate on it from 1999 to 2024, with its active return attributed by sector. The portfolios realise 78.9 to 83.6 basis points a year of tracking error, and each of four covariance estimators forecasts less: the realised active return is 48 to 85 per cent more volatile than forecast. Index changes require 11.4 per cent of the turnover of the portfolio built with Ledoit-Wolf shrinkage. [Page](https://www.carlohofer.com/projects/stock-level-tracking/), [dashboard](https://www.carlohofer.com/stock-level-tracking/dashboard/), [note](https://www.carlohofer.com/stock-level-tracking/note/stock-level-tracking_note_2026-11.pdf), [code](https://github.com/ochofer/stock-level-tracking)

**Rules-based portfolio.** Runs a real-money portfolio under rules published before the first order, with every later change dated in the repository: two UCITS ETFs at 70/30, a monthly cycle with pre-trade checks, look-through exposure and ex-ante risk on a public dashboard. [Page](https://www.carlohofer.com/projects/rules-based-portfolio/), [dashboard](https://www.carlohofer.com/rules-based-portfolio/), [guide](https://www.carlohofer.com/rules-based-portfolio/guide/guide.pdf), [code](https://github.com/ochofer/rules-based-portfolio)

The code, the notebooks and the text are released under the MIT licence (`LICENSE`). French's data are his. His files are downloaded from his library at run time, and the monthly factor returns in the committed tables are his figures as downloaded.

Carlo Hofer, 2026.
