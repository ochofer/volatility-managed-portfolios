# Tables of milestone 1, CRSP vintage 202609

The tables notebooks 01 and 02 wrote to `outputs/` on 10 November 2026, from Ken French's files of vintage 202609, copied here with the provenance record so that every number of the milestone resolves to a file at a named commit. `provenance_french.json` records each file's address, the SHA-256 of its zip and the vintage line. Each notebook regenerates its files at run time into `outputs/`, the run directory; two runs on the same files give the same tables byte for byte. French revises history, so a run on a later vintage, cut at August 2026, is a confirmation run and need not reproduce every digit.

From notebook 01:

- `files_202609.csv`: each file's first block, its rows, and its first and last date.
- `series_202609.csv`: the six factors and WML, with their first month, months, first trading day and trading days.
- `trading_days_per_month_202609.csv`: the market's trading days in each month.
- `samples_202609.csv`: the months each sample holds, beside the N of Moreira and Muir's Table I.

From notebook 02:

- `realised_variance_202609.csv`: the signal of each factor in each month under the three papers' definitions (`mm`, `cowy`, `bsc`).
- `volatility_managed_mm_sample_202609.csv`: each factor's return, last month's realised variance, the position and the volatility-managed return, on Moreira and Muir's sample.
- `position_volatility_managed_202609.csv`: c and the position's 5th, 50th and 95th percentiles and maximum, by factor.
- `real_time_202609.csv`: the real-time combination and the real-time original, month by month to August 2026: the window, c, the weights, the position before and after the cap, and the returns S1 and S2.
- `position_real_time_202609.csv`: the first month with a position, the months, the position's percentiles and maximum, the shares of months below 0 and at the cap, and the median position of the real-time original.
