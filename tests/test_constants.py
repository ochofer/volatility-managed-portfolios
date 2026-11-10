"""The sample windows, the specification count and the expectations, checked as arithmetic on the constants."""
from __future__ import annotations

import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import constants as C  # noqa: E402
from sq import published as P  # noqa: E402


def _months(start: str, end: str) -> int:
    return len(pd.period_range(start, end, freq="M"))


def test_mm_window_reproduces_the_published_n():
    # The end of April 2015 is inferred from these counts; this test is the inference.
    for f in C.FACTORS:
        n = _months(C.FACTOR_FIRST_MONTH[f], C.MM_SAMPLE_END)
        assert n == C.MM_EXPECTED_N[f] == P.MM_TABLE_I[f][4], f
        assert _months(C.FACTOR_FIRST_MONTH[f], "2015-12") == n + 8, f


def test_cowy_after_and_bsc_windows():
    for f in C.FACTORS:
        assert _months(C.FACTOR_FIRST_MONTH[f], C.COWY_SAMPLE_END) == C.COWY_EXPECTED_N[f], f
    assert _months(C.AFTER_START, C.AFTER_END) == C.AFTER_EXPECTED_MONTHS == 136
    assert pd.Period(C.AFTER_START, "M") == pd.Period(C.MM_SAMPLE_END, "M") + 1
    assert _months(C.BSC_FIRST_MONTH, C.BSC_SAMPLE_END) == C.BSC_EXPECTED_MONTHS
    assert pd.Period(C.BSC_FIRST_MONTH, "M") == pd.Period(C.BSC_PAPER_FIRST_MONTH, "M") + 2


def test_specification_count_is_the_list():
    assert len(C.SPECIFICATIONS) == C.SPECIFICATION_COUNT == 38
    assert len(set(C.SPECIFICATIONS)) == len(C.SPECIFICATIONS)


def test_expectations_are_complete_and_dated():
    assert sorted(C.EXPECTATIONS) == ["E1", "E2", "E3", "E4", "E5", "E6"]
    for k, e in C.EXPECTATIONS.items():
        assert set(e) == {"date", "text", "reason"}, k
        assert e["date"] in ("2026-11-08", "2026-11-10"), k
    # The levels quoted in the texts are the levels the code reads.
    assert "0.52" in C.EXPECTATIONS["E1"]["text"] and C.E1_MARKET_SHARPE_BAND == 0.05
    assert "136 months" in C.EXPECTATIONS["E5"]["text"]
    for v in (P.MM_TABLE_V_MARKET["P50"], P.MM_TABLE_V_MARKET["P99"]):
        assert f"{v:.2f}" in C.EXPECTATIONS["E6"]["text"]
    for f in C.FACTORS:
        assert f"{P.COWY_TABLE_1_PANEL_D[f][3]:.2f}" in C.EXPECTATIONS["E6"]["text"], f
    assert f"{P.BSC_TABLE_3_WML[6]:.2f}" in C.EXPECTATIONS["E3"]["text"]
    assert f"{-P.BSC_MAX_DRAWDOWN['WML scaled']:.2f}" in C.EXPECTATIONS["E3"]["text"]
