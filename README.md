In build: milestone 1 of 4, the data and the signal. Nothing in this repository is a result yet.

# Volatility-managed portfolios: a replication, the real-time critique, and the months after the sample

I replicate Moreira and Muir (2017), "Volatility-Managed Portfolios" (Journal of Finance 72(4), 1611-1644), on Ken French's data: a factor's position each month is scaled by the inverse of the factor's realised variance in the month before. I then replicate the real-time critique of Cederburg, O'Doherty, Wang and Yan (2020), "On the performance of volatility-managed portfolios" (Journal of Financial Economics 138(1), 95-117), in which the weights an investor needs are estimated from the data available at the time, and Barroso and Santa-Clara's (2015) scaled momentum as the one robustness check. Sharpe ratio differences are tested with Ledoit and Wolf's (2008) bootstrap. The study's own question is what the signal did in the 136 months after Moreira and Muir's sample, May 2015 to August 2026.

## What is pre-committed

Every sample boundary, construction parameter and expectation is in `src/sq/constants.py`, each with its source and date, written before any code that judges it. The published numbers the replication compares against are in `src/sq/published.py`, each with its page and table; `tests/test_published.py` re-reads them digit by digit from the journal PDFs when the PDFs are present on the machine (they are not in the repository). The study compares 38 pairs of return series; the list is in the same file.

## How to run

Each notebook runs from a blank Google Colab runtime: upload it and run all cells. It writes the code it needs into `src/sq/` and downloads French's files at run time; nothing from French's library is committed. The sample ends at August 2026, fixed in the code (`SAMPLE_END`). A run on a later vintage, cut at August 2026, is a confirmation run: it is labelled by its vintage in the provenance record, it is expected to reproduce every verdict line and every printed decimal and not every digit, because French revises history, and it replaces no committed table without a dated decision.

From a checkout: `pip install -r requirements.txt`, then `python3 -m pytest tests`, then open the notebooks. `build_notebooks.py` regenerates every notebook from its prose and the modules in `src/sq/`; the notebooks are build artefacts and are committed without outputs.

## Terms

- **volatility-managed**: Moreira and Muir's construction, the factor's return times a constant divided by last month's realised variance. Managed describes the construction and says nothing about its performance.
- **real-time combination**: Cederburg, O'Doherty, Wang and Yan's construction, a mix of the volatility-managed and the original factor whose weights are estimated each month from the months before it.
- **the signal**: last month's realised variance of a factor, and nothing else.
- **realised variance**: the variance of a factor computed from the daily returns of one month, each paper with its own definition, given in `src/sq/constants.py`.
- **position**: the multiple of the factor held in a month; the papers call a position above 1 leverage.
- **WML**: winners minus losers, the top momentum decile's return minus the bottom decile's, Barroso and Santa-Clara's momentum series.
- **trading day**: a day on which the New York Stock Exchange traded, one row of French's daily files.
- **vintage**: the version of French's files on the download date, named by the CRSP release they were built from.
- **sample end**: August 2026, the last month any notebook uses, whatever the vintage.

## Layout

```
build_notebooks.py       generates notebooks/ from prose here and code in src/sq/
LICENSE                  the MIT licence
src/sq/constants.py      every pre-committed number, with its source and date
src/sq/published.py      the published numbers of the three papers, with page and table
src/sq/french_loader.py  download, provenance, parsing of French's files, the study's series
src/sq/managed.py        the signal under each paper's definition, the volatility-managed factor, the real-time combination
notebooks/               one concept per notebook, run in order
outputs/                 written at run time: each notebook's tables and the provenance record (not committed)
results/202609/          the tables the milestones cite, copied from outputs/, with the provenance record
tests/                   known-answer checks that run without network
```

## Other projects

**Optimal versus naive diversification.** Under an index-tracking mandate on French's 49 industries, five covariance estimators understate their own tracking error, by 22 to 61 per cent. The replication of DeMiguel, Garlappi and Uppal (2009) reproduces 29 of the 30 Sharpe ratios that carry a band. [Page](https://www.carlohofer.com/projects/optimal-vs-naive-diversification/), [dashboard](https://www.carlohofer.com/optimal-vs-naive-diversification/dashboard/B-P_dashboard.html), [code](https://github.com/ochofer/optimal-vs-naive-diversification)

**Climate risk as an equity signal.** An ownership graph linking 328 listed companies to the 5,115 tracked assets they own. Of 19 apparent ownership changes checked by hand, 12 had no transaction behind them. [Page](https://www.carlohofer.com/projects/climate-risk-equity-signal/), [note](https://github.com/ochofer/paper1-hazard-exposure-data/releases/download/note-v1.2/what-a-vintage-difference-measures.pdf), [code](https://github.com/ochofer/paper1-hazard-exposure-data)

**Rules-based portfolio.** Runs a small real-money portfolio under rules published before the first order: two UCITS ETFs at 70/30, a monthly cycle with pre-trade checks, look-through exposure and ex-ante risk on a public dashboard. [Page](https://www.carlohofer.com/projects/rules-based-portfolio/), [dashboard](https://www.carlohofer.com/rules-based-portfolio/), [code](https://github.com/ochofer/rules-based-portfolio)

The code, the notebooks and the text are released under the MIT licence (`LICENSE`). French's data are his and are downloaded from his library at run time.

Carlo Hofer, 2026.
