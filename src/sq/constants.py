"""
Pre-committed numbers for the study.

Every sample boundary, construction parameter, expectation and test setting is
defined here, one per name, with its source beside it. A notebook may read
these names; it may not introduce numbers of its own. The design was fixed on
8 November 2026 and restated against the three papers' printed tables on
10 November 2026, before any code that judges an expectation was written.

The three papers, with the journal's page numbers used throughout:

  MM    Moreira and Muir (2017), "Volatility-Managed Portfolios", Journal of
        Finance 72(4), 1611-1644.
  COWY Cederburg, O'Doherty, Wang and Yan (2020), "On the performance of
        volatility-managed portfolios", Journal of Financial Economics 138(1),
        95-117.
  BSC   Barroso and Santa-Clara (2015), "Momentum has its moments", Journal of
        Financial Economics 116(1), 111-120.

The Sharpe ratio test is Ledoit and Wolf (2008), "Robust performance
hypothesis testing with the Sharpe ratio", Journal of Empirical Finance 15(5),
850-859. The published numbers the expectations compare against are typed in
src/sq/published.py, never here.
"""

# ---------------------------------------------------------------------------
# 1. Data: Ken French's library, downloaded at run time, never committed
# ---------------------------------------------------------------------------

FRENCH_BASE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"

# Every file the study reads. The vintage is whatever the library serves on the
# download date; the loader records the date, the SHA-256 of the zip and the
# CRSP vintage line printed at the top of each CSV.
FRENCH_FILES = {
    "factors3":       "F-F_Research_Data_Factors_CSV.zip",             # Mkt-RF, SMB, HML, RF, monthly from 1926-07
    "factors3_daily": "F-F_Research_Data_Factors_daily_CSV.zip",       # the same, daily from 1926-07-01
    "factors5":       "F-F_Research_Data_5_Factors_2x3_CSV.zip",       # adds RMW and CMA, monthly from 1963-07
    "factors5_daily": "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip", # the same, daily from 1963-07-01
    "momentum":       "F-F_Momentum_Factor_CSV.zip",                   # Mom, monthly from 1927-01
    "momentum_daily": "F-F_Momentum_Factor_daily_CSV.zip",             # Mom, daily from 1926-11-03
    "mom10":          "10_Portfolios_Prior_12_2_CSV.zip",              # ten portfolios formed on momentum, monthly from 1927-01
    "mom10_daily":    "10_Portfolios_Prior_12_2_Daily_CSV.zip",        # the same, daily from 1926-11-03
}

FRENCH_MISSING_CODES = (-99.99, -999.0)   # French's own convention, stated at the top of every portfolio file
FRENCH_RETURNS_ARE_PERCENT = True         # the loader divides by 100 once, at load time, and nowhere else

# The six factors, by French's column names, and the file each comes from.
# Mkt-RF, SMB and HML come from the three-factor file, as in MM Table I and
# COWY section 2.1 (Fama and French 1993); RMW and CMA from the five-factor
# file (Fama and French 2015); Mom from the momentum file. RF is the
# three-factor file's one-month Treasury bill return.
FACTORS = ("Mkt-RF", "SMB", "HML", "Mom", "RMW", "CMA")
FACTOR_SOURCE = {
    "Mkt-RF": "factors3", "SMB": "factors3", "HML": "factors3",
    "Mom": "momentum", "RMW": "factors5", "CMA": "factors5",
}
RF_SOURCE = "factors3"

# WML, the momentum series of BSC: the top decile minus the bottom decile of
# the ten value-weighted portfolios formed on returns from month t-12 to t-2
# (BSC Appendix A, p. 119). Block 0 of both files holds the value-weighted returns.
WML_LONG = "Hi PRIOR"
WML_SHORT = "Lo PRIOR"
WML_BLOCK = 0
WML_BLOCK_TITLE_MUST_CONTAIN = "Value Weight"

# The end of the sample, fixed on 8 November 2026: August 2026 on any vintage.
# The loader cuts every file at this month, so that each notebook sees the same
# months on any later vintage; the vintage line and the SHA-256 in the
# provenance record say which revision of French's history a run used. A run on
# a later vintage, cut at August 2026, is a confirmation run: it is labelled by
# its vintage in the provenance record, it is expected to reproduce every
# verdict line and every printed decimal and not every digit, because French
# revises history, and it replaces no committed table without a dated decision.
SAMPLE_END = "2026-08"
SAMPLE_END_RULE_DATE = "2026-11-08"
CONFIRMATION_RUN = "a run on a later vintage, cut at August 2026, labelled by its vintage in the provenance record"

# French's daily files carry Saturday trading days until 24 May 1952. The number of
# trading days in a calendar month runs from 17 to 27 before June 1952 and from 15
# to 23 from 1953 on (counted on vintage 202609). Months with fewer trading days
# than the level below are flagged and reported; none is dropped.
LAST_SATURDAY_TRADING_DAY = "1952-05-24"
TRADING_DAYS_FLAG_BELOW = 15

PROVENANCE_FILE = "outputs/provenance_french.json"   # download date, URL, SHA-256 and CRSP vintage line per file
TIMEZONE = "Europe/Amsterdam"

# ---------------------------------------------------------------------------
# 2. The samples
# ---------------------------------------------------------------------------

# The first month with a volatility-managed return, for each factor: the month
# after the first month of daily data, or the first month of the monthly file
# if that is later. These are COWY's start dates (Table 1 note, p. 99).
FACTOR_FIRST_MONTH = {
    "Mkt-RF": "1926-08", "SMB": "1926-08", "HML": "1926-08",
    "Mom": "1927-01", "RMW": "1963-08", "CMA": "1963-08",
}

# MM's sample. The paper says "1926 to 2015" (Table I note, p. 1619) and prints
# N = 1,065 for Mkt, SMB and HML, 1,060 for Mom and 621 for RMW and CMA. From
# the first months above, all three counts end in April 2015 exactly; an end in
# December 2015 would give 1,073, 1,068 and 629. The paper does not state the
# months, so the end is inferred from these counts; the computed N is reported
# beside the published N in every table that judges E1.
MM_SAMPLE_END = "2015-04"
MM_SAMPLE_END_IS_INFERRED = True
MM_EXPECTED_N = {"Mkt-RF": 1065, "SMB": 1065, "HML": 1065, "Mom": 1060, "RMW": 621, "CMA": 621}

# COWY's sample: the same first months to December 2016 (Table 1 note, p. 99).
COWY_SAMPLE_END = "2016-12"
COWY_EXPECTED_N = {"Mkt-RF": 1085, "SMB": 1085, "HML": 1085, "Mom": 1080, "RMW": 641, "CMA": 641}

# The months after MM's sample, the study's own question (E5).
AFTER_START = "2015-05"
AFTER_END = SAMPLE_END
AFTER_EXPECTED_MONTHS = 136

# BSC's sample is 1927:03 to 2011:12 (Table 3, p. 116). Their daily WML starts
# in August 1926 (Daniel and Moskowitz's data, Appendix A, p. 119); French's
# daily file of the ten momentum portfolios starts on 3 November 1926, so the
# 126 trading days the variance needs are first available at the end of April 1927
# and the first scaled month is May 1927, two months after the paper's.
BSC_PAPER_FIRST_MONTH = "1927-03"
BSC_FIRST_MONTH = "1927-05"
BSC_SAMPLE_END = "2011-12"
BSC_EXPECTED_MONTHS = 1016          # May 1927 to December 2011 inclusive
BSC_EXTENDED_END = SAMPLE_END       # the second period of scaled momentum: May 1927 to August 2026

# ---------------------------------------------------------------------------
# 3. The constructions
# ---------------------------------------------------------------------------

# The signal: last month's realised variance of the factor's daily returns.
# Each construction uses its own paper's definition.
#
# MM equation 2, p. 1616: each day's return minus the month's mean, squared and
# summed over the month. The equation is written for a 22-day month; the mean
# here is the month's own mean, the sum of its daily returns divided by its
# number of trading days.
RV_MM = "sum over the month's trading days of (daily return minus the month's mean daily return) squared"
# COWY equation 4, p. 98: 22 divided by the month's number of trading days J,
# times the sum of squared daily returns; no mean is removed.
RV_COWY_DAYS = 22
RV_COWY = "22 / J times the sum over the month's J trading days of the squared daily return"
# BSC equation 5, p. 115: 21 times the mean squared daily return over the last
# 126 trading days up to the month's last trading day, a monthly variance.
RV_BSC_TRADING_DAYS = 126
RV_BSC_DAYS_PER_MONTH = 21

# Which definition each comparison uses: a comparison with a paper's printed
# numbers uses that paper's definition. Fixed 10 November 2026.
RV_BY_COMPARISON = {
    "volatility-managed factor on MM's sample: E1, E4, E6 (Table IV, Table V)": "MM",
    "volatility-managed factor on COWY's sample: E2 (i), E6 (Table 1, Panel D)": "COWY",
    "real-time combination and real-time original: E2 (ii) to (iv), E5": "COWY",
    "volatility-managed factor after the sample, c fixed to April 2015: E5, no verdict": "MM",
    "scaled WML: E3": "BSC",
}

# The volatility-managed factor (MM equation 1, p. 1616): f_sigma_t = (c / RV_{t-1}) f_t,
# with c set so that the managed and the original factor have the same standard
# deviation over the sample the comparison runs on. c does not change a Sharpe
# ratio or an appraisal ratio (MM footnote 6, p. 1616; COWY p. 98).
#
# The real-time combination (COWY section 4.3, pp. 106-107, Table 5 Panel A):
# at the start of each month t after an initial training period of K months,
# on an expanding window of all months before t,
#   1. c_t gives the managed and the original factor the same variance over the window;
#   2. the means mu and the covariance Sigma of the managed and the original factor
#      are estimated over the window;
#   3. the weights are (x_sigma, x) = (1 / gamma) Sigma^-1 mu;
#   4. the position in the original factor is y_t = x_sigma c_t / RV_{t-1} + x, with |y_t| <= cap;
#   5. the month's return is y_t f_t.
# S2, the real-time original, is the same with the original factor alone:
# y_t = (1 / gamma) mu / sigma^2, under the same cap. S3, the ex post optimal
# combination, uses the moments of the whole out-of-sample period.
REALTIME_K = 120               # months; COWY p. 106, "K = 120 months"
REALTIME_GAMMA = 5.0           # risk aversion; COWY Table 5 note, p. 106
REALTIME_LEVERAGE_CAP = 5.0    # |y_t| <= 5; COWY Table 5 note, p. 106, and p. 107
REALTIME_WINDOW = "expanding"  # COWY p. 106

# Scaled momentum (BSC equation 6, p. 115): WML scaled by sigma_target / sigma_hat_{t-1},
# sigma_hat the square root of equation 5's variance, sigma_target an annualised
# volatility of 12 per cent (BSC p. 115), here as a monthly figure.
BSC_TARGET_VOL_ANNUAL = 0.12
BSC_TARGET_VOL_MONTHLY = BSC_TARGET_VOL_ANNUAL / 12 ** 0.5

# ---------------------------------------------------------------------------
# 4. Measures and tests (the decisions with defaults of 8 November 2026)
# ---------------------------------------------------------------------------

MONTHS_PER_YEAR = 12
# The regression f_sigma_t = alpha + beta f_t + e_t, monthly. Alpha is reported
# in per cent a year (times 12); the appraisal ratio is alpha / sd(e) times the
# square root of 12 (MM footnote 11, p. 1620); Sharpe ratios are annualised by
# the square root of 12.
ALPHA_ANNUALISE = MONTHS_PER_YEAR
SHARPE_ANNUALISE = MONTHS_PER_YEAR ** 0.5

# Standard errors. E1 is judged with heteroskedasticity-robust standard errors,
# the papers' own (MM Table I note, p. 1619; COWY Table 3 note, White 1980,
# p. 104). The Newey and West standard error at 12 lags is reported beside it
# and is the one E4 to E6 use. HML's published alpha, 1.97 with a standard
# error of 1.02, has a t-statistic of 1.93 against the 1.96 line, so the
# choice can move a factor across it.
SE_E1 = "HC0"                  # White (1980)
NEWEY_WEST_LAGS = 12
SIGNIFICANCE_LEVEL = 0.05

# The Sharpe ratio difference (Ledoit and Wolf 2008): the studentised circular
# block bootstrap on paired series.
BOOTSTRAP_BLOCK_MONTHS = 12
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_LEVEL = 0.95
BOOTSTRAP_SEED = 20261108      # the date of the design, as a number

# The size check, run before the test touches a factor: 1,000 simulated pairs
# with equal Sharpe ratios and the sample's length, Student-t shocks with five
# degrees of freedom, a common component with the market's correlation between
# the pair, no difference in means.
SIZE_CHECK_PAIRS = 1000
SIZE_CHECK_T_DOF = 5
SIZE_CHECK_SEED = 20261110

# Costs: one proportional cost per unit of one-way turnover, the turnover of a
# volatility-managed strategy in a month being the absolute change in its
# position, |w_t - w_{t-1}|. Factor portfolios are traded through liquid
# large-cap long-short books, for which 10 basis points per unit of notional
# traded is the order the literature on implementation costs reports (MM Table
# IV, p. 1625, takes 10 basis points from Frazzini, Israel and Moskowitz); the
# one sensitivity doubles it.
COST_PER_TURNOVER = 0.0010
COST_SENSITIVITY = 0.0020

# ---------------------------------------------------------------------------
# 5. The specifications, counted before the code runs
# ---------------------------------------------------------------------------

# A specification is one pair of return series compared on one sample. The
# list is written out so that nothing can be added after a run without a dated
# disclosure. Cost levels are sensitivities of the same specifications and are
# not counted again.
_SAMPLES = {
    "MM": "first month to April 2015",
    "COWY": "first month to December 2016",
    "AFTER": "May 2015 to August 2026",
}
SPECIFICATIONS = (
    tuple(("E1", f, "MM", "volatility-managed", "original") for f in FACTORS)
    + tuple(("E2 (i)", f, "COWY", "volatility-managed", "original") for f in FACTORS)
    + tuple(("E2 (ii, iii)", f, "COWY", "real-time combination S1", "real-time original S2") for f in FACTORS)
    + tuple(("E2 (iv)", f, "COWY", "real-time combination S1", "ex post optimal combination S3") for f in FACTORS)
    + tuple(("E5", f, "AFTER", "real-time combination S1", "real-time original S2") for f in FACTORS)
    + tuple(("E5, no verdict", f, "AFTER", "volatility-managed, c to April 2015", "original") for f in FACTORS)
    + (("E3", "WML", "BSC 1927-05 to 2011-12", "scaled WML", "WML"),
       ("E3, extended", "WML", "BSC 1927-05 to 2026-08", "scaled WML", "WML"))
)
SPECIFICATION_COUNT = 38
SPECIFICATION_COUNT_DATE = "2026-11-10"

# ---------------------------------------------------------------------------
# 6. The expectations, written before the code
# ---------------------------------------------------------------------------

# Each is a strict pass or fail, reported in the same voice whether met or
# not; no level moves after a run. The levels the code reads are the named
# constants; the text and the reason are what each notebook quotes.

E1_MIN_FACTORS = 5
E1_ALPHA_WITHIN_SE = 1.0
E1_APPRAISAL_BAND = 0.05
E1_MARKET_SHARPE_BAND = 0.05

E2_SHARPE_BAND = 0.05
E2_SIGN_MIN_FACTORS = 5
E2_ONLY_SIGNIFICANT = ("Mom",)
E2_S1_S3_BAND = 0.05

E3_SHARPE_BAND = 0.05
E3_DRAWDOWN_BAND = 0.05        # five percentage points of drawdown

E4_SIZE_RANGE = (0.035, 0.065)
E4_MIN_FACTORS = 5

E5_MAX_FACTORS_ABOVE = 2

E6_COST = COST_PER_TURNOVER
E6_MIN_NW_T = 2.0
E6_MARKET_PERCENTILES = (50, 75, 90, 99)
E6_PERCENTILE_BAND = 0.15      # P50, P75 and P90
E6_P99_BAND = 1.0

EXPECTATIONS = {
    "E1": {
        "date": "2026-11-10",
        "text": (
            "On MM's sample (each factor's first month to April 2015), for at least five of the six factors: "
            "the alpha's sign and its 5 per cent significance category, with heteroskedasticity-robust (White) "
            "standard errors, match Table I (p. 1619); the alpha lies within one published standard error of the "
            "published alpha; and the appraisal ratio, computed from Table I's alpha and RMSE with footnote 11's "
            "annualisation (p. 1620), lies within 0.05 of the paper's figure, the market's 0.33 from the table, with "
            "the text's 0.34 (p. 1620) and 0.33 (p. 1612) noted beside it. For the market, the volatility-managed "
            "Sharpe ratio also lies within 0.05 of 0.52 (Table V, Panel A, p. 1626), and the market counts as "
            "matching only if it does. Every factor's comparisons are reported, whatever the count, with the "
            "computed N beside the published N."
        ),
        "reason": (
            "The replication criterion fixed on 6 September 2026: sign and significance, one standard error, and a "
            "band of 0.05. Its Sharpe ratio leg is the appraisal ratio for every factor because the paper prints no "
            "Sharpe ratio for any factor but the market. French revises history, so exact equality is not expected; "
            "five of six allows one factor to miss on a revised series, and the miss is reported, not chased."
        ),
    },
    "E2": {
        "date": "2026-11-10",
        "text": (
            "On COWY's sample (August 1926, January 1927 or August 1963 to December 2016), for each of the six "
            "factors: (i) the original and the volatility-managed Sharpe ratios lie within 0.05 of their Table 1 "
            "(p. 99); (ii) the real-time combination's Sharpe ratio S1 and the real-time original's S2 lie within "
            "0.05 of Table 5, Panel A (p. 106); (iii) S1 minus S2 has the published sign for at least five of the "
            "six, and the only difference significant at 5 per cent by the Jobson and Korkie test is momentum's, "
            "as published; (iv) S1 minus S3, the ex post optimal combination, lies within 0.05 of the published "
            "figure for all six. All twenty-four comparisons are reported, whatever the count."
        ),
        "reason": (
            "The critique's baseline is a real-time combination of the volatility-managed and the original factor "
            "(section 4.3, pp. 106-107): the scaling constant alone does not move a Sharpe ratio (MM footnote 6, "
            "p. 1616; COWY p. 98), and the weights of the combination are what an investor cannot know in advance."
        ),
    },
    "E3": {
        "date": "2026-11-10",
        "text": (
            "On May 1927 to December 2011, the Sharpe ratios of unscaled and scaled WML lie within 0.05 of 0.53 and "
            "0.97 (BSC Table 3, p. 116), and the maximum drawdowns lie within five percentage points of 96.69 and "
            "45.20 per cent (p. 112). The first scaled month is two months after the paper's 1927:03 because "
            "French's daily file of the ten momentum portfolios starts on 3 November 1926."
        ),
        "reason": (
            "The paper's two headline results, on its own momentum series (Appendix A, p. 119); the Sharpe band is "
            "the one used throughout the study."
        ),
    },
    "E4": {
        "date": "2026-11-08",
        "text": (
            "The size check rejects between 3.5 and 6.5 per cent of the 1,000 simulated null pairs at the 5 per cent "
            "level; and on MM's sample the bootstrap's verdict on the Sharpe ratio difference agrees in sign and in "
            "significance with the Newey and West t-statistic on the alpha for at least five of the six factors."
        ),
        "reason": (
            "A test that is wrong about its own size is not used; the band is two standard errors of a proportion "
            "of 0.05 over 1,000 draws. The alpha and the Sharpe ratio difference are two readings of the same gain "
            "and should agree."
        ),
    },
    "E5": {
        "date": "2026-11-10",
        "text": (
            "On the months after MM's sample, May 2015 to August 2026 (136 months), with the paper's c fixed on the "
            "data to April 2015 and the real-time combination carried forward from its expanding window: for each "
            "factor, the Sharpe ratio of the real-time combination against the real-time original S2, as in COWY "
            "Table 5, and of the volatility-managed factor against the original factor itself, each difference with "
            "its Ledoit and Wolf bootstrap interval. On at most two of the six factors the real-time combination's "
            "Sharpe ratio exceeds S2's by more than the interval allows, and the median across the six of the Sharpe "
            "difference lies within plus or minus the median of the six intervals' half-widths. The same two counts "
            "are reported for the volatility-managed factor, in no verdict."
        ),
        "reason": (
            "The study's own question, with the prior the critique gives: gains an investor could not have set in "
            "real time should show little in months neither paper could have known. If more than two factors clear "
            "the interval, the expectation fails and the finding is reported as such."
        ),
    },
    "E6": {
        "date": "2026-11-10",
        "text": (
            "At 10 basis points per unit of turnover, the market's volatility-managed alpha over MM's sample stays "
            "positive and more than two Newey and West standard errors from zero (the paper: 3.98 per cent a year at "
            "10 basis points, an average absolute change in weight of 0.73 and a break-even cost of 56 basis points, "
            "Table IV, p. 1625). On MM's sample, the market's P50, P75 and P90 of the leverage lie within 0.15 of "
            "0.93, 1.59 and 2.64, and its P99 within 1.0 of 6.39 (Table V, Panel A, p. 1626); on COWY's sample, each "
            "factor's P50 lies within 0.15 of their Table 1, Panel D (p. 99), and its P99 within 1.0 of theirs (6.47, "
            "5.07, 5.89, 8.64, 5.02, 4.56)."
        ),
        "reason": (
            "MM report that the market strategy's gain survives moderate costs (Table IV) and print the distribution "
            "of its leverage (Table V); COWY print the 1st, 50th and 99th percentiles for every factor. The "
            "expectation says whether both hold on this vintage."
        ),
    },
}
