# Tables of milestones 1 to 3, Ken French's files of vintage 202609

The tables notebooks 01 to 08 wrote to `outputs/` (notebooks 01 to 05 on 10 November 2026, 06 to 08 on 12 November), from Ken French's files of vintage 202609, copied here with the provenance record so that every number of the milestone resolves to a file at a named commit. `provenance_french.json` records each file's address, the SHA-256 of its zip and the vintage line. Each notebook regenerates its files at run time into `outputs/`, the run directory; two runs on the same files give the same tables byte for byte. French revises history, so a run on a later vintage, cut at August 2026, is a confirmation run and need not reproduce every digit.

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

From notebook 03 (E1):

- `mm_table_i_computed_202609.csv`: Moreira and Muir's Table I as computed, for each factor: beta, alpha and its White and Newey-West standard errors, N, R², RMSE, the appraisal ratio and both Sharpe ratios.
- `e1_comparison_202609.csv`: every number E1 judges beside the published one, with each comparison's result.
- `e1_verdict_202609.csv`: the factors matching, the number required and the verdict.

From notebook 04 (E2):

- `cowy_table_1_computed_202609.csv`: Cederburg et al.'s Table 1 as computed beside the published numbers: means, standard deviations and Sharpe ratios of the original and the volatility-managed factors, their difference and its Jobson-Korkie p-value.
- `cowy_table_5_computed_202609.csv`: their Table 5, Panel A, as computed beside the published numbers: S1, S2 and S3, the two differences with their p-values, the share of months at the cap and S3's weights.
- `e2_comparison_202609.csv`: the four comparisons of E2 for each factor, computed beside published, with each one's result.
- `e2_verdict_202609.csv`: the comparisons holding, each clause's result and the verdict.
- `e2_cause_original_factors_202609.csv`: each original factor's mean and standard deviation over its Table 1 months beside Table 1's, and the Sharpe ratios they give.
- `e2_diagnostic_a_rmw_mean_moved_202609.csv`: diagnostic (a), computed after the result and carrying no verdict: RMW's comparisons rebuilt with its monthly returns moved by one constant to Table 1's mean.
- `e2_diagnostic_b_rmw_archived_202609.csv`: diagnostic (b), computed after the result and carrying no verdict: RMW's mean and standard deviation over August 1963 to December 2016 in the Internet Archive's copy of French's five-factor file of 9 July 2017, beside Table 1's and this vintage's. The archived file itself is fetched at run time and not committed.

From notebook 05 (E3):

- `bsc_table_3_computed_202609.csv`: Barroso and Santa-Clara's Table 3 as computed beside the published numbers, for WML and scaled WML.
- `e3_comparison_202609.csv`: the two Sharpe ratios and the two maximum drawdowns beside the published ones, with each comparison's result.
- `e3_verdict_202609.csv`: the comparisons holding and the verdict.
- `scaled_wml_to_sample_end_202609.csv`: WML and scaled WML on May 1927 to August 2026, which no expectation judges.
- `scaled_wml_series_202609.csv`: WML, last month's volatility, the weight and scaled WML, month by month from May 1927 to August 2026.

From notebook 06 (E4):

- `size_check_202609.csv`: the size check's settings (months, the market's monthly mean and standard deviation, the correlation, the degrees of freedom, the seed, the draws, the block) and its rejection rate.
- `sharpe_tests_mm_sample_202609.csv`: for each factor on Moreira and Muir's sample, the alpha and its Newey-West t-statistic beside both Sharpe ratios, their difference, its Ledoit-Wolf interval and p-value, annualised.
- `e4_comparison_202609.csv`: each factor's sign and significance under both tests, the strict count and the count by category.
- `e4_verdict_202609.csv`: the size rate, both parts, both counts and the verdict.
- `alpha_and_sharpe_difference_202609.csv`: for each factor, both sides of the identity that links the alpha to the Sharpe ratio difference.

From notebook 07 (E5):

- `after_sample_series_202609.csv`: May 2015 to August 2026, for each factor, the original and volatility-managed returns, the position with c fixed to April 2015, the real-time combination and the real-time original with their positions and windows.
- `after_sample_sharpe_202609.csv`: the four Sharpe ratios on those 136 months.
- `e5_real_time_tests_202609.csv`: the real-time combination against the real-time original, with the Ledoit-Wolf interval and p-value, annualised.
- `e5_volatility_managed_tests_202609.csv`: the volatility-managed factor against the original, in no verdict.
- `e5_verdict_202609.csv`: the two counts of E5, the verdict, and the same counts for the volatility-managed factor in no verdict.

From notebook 08 (E6):

- `costs_mm_sample_202609.csv`: for each factor on Moreira and Muir's sample, the average turnover, the alpha gross and net of 10 and 20 basis points with Newey-West standard errors and t-statistics, and the break-even cost.
- `position_market_mm_sample_202609.csv`: the market's P50, P75, P90, P99 and maximum position on Moreira and Muir's sample.
- `position_cowy_sample_202609.csv`: each factor's P1, P50, P99 and maximum position on Cederburg et al.'s sample, beside the published ones.
- `e6_comparison_202609.csv`: the seventeen comparisons of E6, each with its level and result.
- `e6_verdict_202609.csv`: the comparisons holding and the verdict.
