"""Loader checks on small files shaped like French's CSVs, with no network."""
from __future__ import annotations

import io
import pathlib
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sq import constants as C  # noqa: E402
from sq import french_loader as fl  # noqa: E402

PORTFOLIOS = """This file was created using the 202609 CRSP database.
It contains value- and equal-weighted returns for portfolios formed on prior returns.

Missing data are indicated by -99.99 or -999.


 Value Weight Returns -- Monthly
,Lo PRIOR,PRIOR 2,Hi PRIOR
192701,  -2.00,   0.50,   3.00
192702,   1.00, -99.99,  -1.00
192703,   0.10,   0.20,   0.30

  Average Equal Weighted Returns -- Monthly
,Lo PRIOR,PRIOR 2,Hi PRIOR
192701,  -9.00,   9.00,   9.00
192702,   9.00,   9.00,   9.00
192703,   9.00,   9.00,   9.00

  Average Value Weighted Returns -- Annual
,Lo PRIOR,PRIOR 2,Hi PRIOR
1927,  10.00,  11.00,  12.00

  Number of Firms in Portfolios
,Lo PRIOR,PRIOR 2,Hi PRIOR
192701,     12,     25,     30
192702,     12,     25,     30
192703,     12,     26,     31
"""

FACTORS3 = """This file was created by using the 202609 CRSP database.
The 1-month TBill return is from Ibbotson and Associates, Inc.

,Mkt-RF,SMB,HML,RF
192607,   2.89,  -2.55,  -2.39,   0.22
192608,   2.64,  -1.14,   3.81,   0.25
192609,   0.38,  -1.36,   0.05,   0.23

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
1927,  29.47,  -2.04,  -4.54,   3.12
"""

MOMENTUM = """This file was created using the 202609 CRSP database.
Missing data are indicated by -99.99 or -999.

,Mom
192609,   0.56
"""

FACTORS5 = """This file was created using the 202609 CRSP database.
The 1-month TBill return is from Ibbotson and Associates Inc.

,Mkt-RF,SMB,HML,RMW,CMA,RF
192609,   0.38,  -1.36,   0.05,   1.00,  -1.00,   0.23
"""

DAILY = """This file was created by using the 202609 CRSP database.
The Tbill return is the simple daily rate.

,Mkt-RF,SMB,HML,RF
19520522,   0.36,   0.09,  -0.10,   0.01
19520523,  -0.23,   0.71,   0.10,   0.01
19520524,   0.50,  -1.00,   0.30,   0.01
19520602,   0.10,   0.20,   0.30,   0.01
"""


def _zip(path: pathlib.Path, text: str) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(path.name.replace("_CSV.zip", ".csv"), text)


def test_parse_blocks_shapes_and_titles():
    blocks = fl.parse_blocks(PORTFOLIOS)
    assert [b["title"] for b in blocks] == [
        "Value Weight Returns -- Monthly",
        "Average Equal Weighted Returns -- Monthly",
        "Average Value Weighted Returns -- Annual",
        "Number of Firms in Portfolios",
    ]
    assert [b["frequency"] for b in blocks] == ["monthly", "monthly", "annual", "monthly"]
    first = blocks[0]["frame"]
    assert list(first.columns) == ["Lo PRIOR", "PRIOR 2", "Hi PRIOR"]
    assert str(first.index[0]) == "1927-01" and first.loc["1927-03", "Hi PRIOR"] == 0.30


def test_untitled_factor_block_and_vintage_line():
    blocks = fl.parse_blocks(FACTORS3)
    assert blocks[0]["title"].startswith("(untitled") and blocks[0]["frequency"] == "monthly"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("x.csv", FACTORS3)
    assert fl._vintage_line(buf.getvalue()) == "This file was created by using the 202609 CRSP database."


def test_daily_dates_are_days_and_saturdays_are_rows():
    frame = fl.parse_blocks(DAILY)[0]["frame"]
    assert frame.index.freqstr == "D" and len(frame) == 4
    assert frame.index[2].to_timestamp().day_name() == "Saturday"   # 24 May 1952, the last Saturday trading day
    counts = fl.trading_days_per_month(frame)
    assert counts.loc["1952-05"] == 3 and counts.loc["1952-06"] == 1


def test_wml_is_top_minus_bottom_decile_in_decimals(tmp_path):
    _zip(tmp_path / C.FRENCH_FILES["mom10"], PORTFOLIOS)
    w = fl.wml("monthly", cache_dir=tmp_path)
    assert w.name == "WML"
    assert abs(w.loc["1927-01"] - 0.05) < 1e-12        # 3.00 - (-2.00) per cent
    assert abs(w.loc["1927-02"] - (-0.02)) < 1e-12
    assert w.attrs["provenance"]["vintage_line"].endswith("202609 CRSP database.")


def test_factors_assembles_six_columns_and_masks_missing(tmp_path):
    _zip(tmp_path / C.FRENCH_FILES["factors3"], FACTORS3)
    _zip(tmp_path / C.FRENCH_FILES["momentum"], MOMENTUM)
    _zip(tmp_path / C.FRENCH_FILES["factors5"], FACTORS5)
    f = fl.factors("monthly", cache_dir=tmp_path)
    assert list(f.columns) == list(C.FACTORS) + ["RF"]
    assert abs(f.loc["1926-07", "Mkt-RF"] - 0.0289) < 1e-12
    assert np.isnan(f.loc["1926-07", "Mom"]) and np.isnan(f.loc["1926-08", "RMW"])   # later files start later
    assert abs(f.loc["1926-09", "CMA"] - (-0.01)) < 1e-12
    assert len(f.attrs["provenance"]) == 3


def test_the_sample_end_cuts_monthly_daily_and_annual_blocks(monkeypatch):
    monkeypatch.setattr(C, "SAMPLE_END", "2026-08")
    monthly = pd.DataFrame({"a": range(5)}, index=pd.period_range("2026-05", periods=5, freq="M"))
    daily = pd.DataFrame({"a": range(70)}, index=pd.period_range("2026-07-20", periods=70, freq="D"))
    annual = pd.DataFrame({"a": range(3)}, index=pd.period_range("2025", periods=3, freq="Y"))
    assert str(fl.cut_to_sample_end(monthly).index[-1]) == "2026-08" and len(fl.cut_to_sample_end(monthly)) == 4
    assert str(fl.cut_to_sample_end(daily).index[-1]) == "2026-08-31"
    assert str(fl.cut_to_sample_end(annual).index[-1]) == "2026"
    early = pd.DataFrame({"a": range(3)}, index=pd.period_range("2026-01", periods=3, freq="M"))
    assert fl.cut_to_sample_end(early).equals(early)
    monkeypatch.setattr(C, "SAMPLE_END", None)
    assert len(fl.cut_to_sample_end(monthly)) == 5
