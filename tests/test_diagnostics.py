"""The diagnostics: the shift hits its target mean and leaves the standard deviation alone, and the archived
file is read from its cached copy without a network."""
from __future__ import annotations

import io
import pathlib
import sys
import zipfile

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import diagnostics as D  # noqa: E402


def test_shift_to_mean_hits_the_target_and_keeps_the_standard_deviation():
    idx = pd.period_range("1963-07", "2017-03", freq="M")
    f = pd.Series(np.random.default_rng(5).normal(0.003, 0.02, len(idx)), index=idx, name="RMW")
    shifted, delta = D.shift_to_mean(f, "1963-08", "2016-12", 2.92)
    assert shifted.loc["1963-08":"2016-12"].mean() * 1200 == pytest.approx(2.92)
    assert shifted.std() == pytest.approx(f.std())
    assert (f - shifted).to_numpy() == pytest.approx(np.full(len(f), delta))


ARCHIVED = """This file was created by CMPT_ME_BEME_OP_INV_RETS using the 201705 CRSP database.
The 1-month TBill return is from Ibbotson and Associates Inc.

,Mkt-RF,SMB,HML,RMW,CMA,RF
196307,   -0.39,   -0.46,   -0.82,    0.72,   -1.16,    0.27
196308,    5.07,   -0.81,    1.63,    0.42,   -0.40,    0.25

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RMW,CMA,RF
1964,   12.54,    0.95,    9.24,    1.40,    6.35,    3.54
"""


def test_archived_file_is_read_from_its_cached_copy(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("F-F_Research_Data_5_Factors_2x3.CSV", ARCHIVED)
    (tmp_path / f"F-F_Research_Data_5_Factors_2x3_CSV_{D.ARCHIVE_TIMESTAMP}.zip").write_bytes(buf.getvalue())
    frame, record = D.archived_five_factor(tmp_path)
    assert list(frame.columns) == ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
    assert frame.loc["1963-08", "RMW"] == pytest.approx(0.0042)
    assert record["vintage_line"].endswith("201705 CRSP database.")
    assert record["sha256_as_read_on_10_november"] is False      # the fixture is not the archived file
    assert record["capture"] == "9 July 2017" and record["address"].startswith("https://web.archive.org/web/20170709190513/")
