"""
Diagnostics: checks computed after a verdict, to read its cause. None of them
carries a verdict, and none changes a level in constants.py.

E2's diagnostics (notebook 04), allowed by the design on 10 November 2026:

  (a) shift_to_mean: the original factor's monthly returns moved by one
      constant so that their mean over given months equals a published mean.
      Rebuilding a comparison from the shifted series shows how much of a gap
      the mean alone accounts for. The daily returns, and so the signal, are
      left as they are.

  (b) archived_five_factor: French's five-factor file as the Internet Archive
      holds it from 2017, the copy closest in time to Cederburg et al.'s
      download. It is fetched at run time into data/archive/, never committed,
      and read for the original factors' means and standard deviations only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import requests

from . import constants as C
from . import french_loader as fl

# The Internet Archive's only capture of the file in 2017 and 2018 (its CDX
# index, read on 10 November 2026). The "id_" form of the address returns the
# file's bytes as captured.
ARCHIVE_TIMESTAMP = "20170709190513"
ARCHIVE_DATE = "9 July 2017"
ARCHIVE_ORIGINAL = "http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"
ARCHIVE_PAGE = f"https://web.archive.org/web/{ARCHIVE_TIMESTAMP}/{ARCHIVE_ORIGINAL}"
ARCHIVE_URL = f"https://web.archive.org/web/{ARCHIVE_TIMESTAMP}id_/{ARCHIVE_ORIGINAL}"
ARCHIVE_SHA256 = "24553b6d6b93bfd58d0a87a6859d599e75df2db24c85631f693b7ed7ef493ae8"


def shift_to_mean(f: pd.Series, start: str, end: str, target_annual_percent: float) -> tuple[pd.Series, float]:
    """The series f with one constant subtracted from every month, chosen so that its mean over the months
    start to end equals target_annual_percent (per cent a year, monthly mean times 12). Returns the shifted
    series and the constant, a monthly decimal."""
    delta = float(f.loc[start:end].mean() - target_annual_percent / 100 / C.MONTHS_PER_YEAR)
    return (f - delta).rename(f.name), delta


def archived_five_factor(cache_dir: str | Path = "data/archive") -> tuple[pd.DataFrame | None, dict]:
    """The monthly block of the archived five-factor file in decimal returns, with a record of the
    capture: its date, address, SHA-256 and first line. Returns (None, record with the error) when the
    archive cannot be reached, so that the notebook says so and goes on."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"F-F_Research_Data_5_Factors_2x3_CSV_{ARCHIVE_TIMESTAMP}.zip"
    record = {"capture": ARCHIVE_DATE, "address": ARCHIVE_PAGE}
    try:
        if not path.exists():
            response = requests.get(ARCHIVE_URL, timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
    except requests.RequestException as err:
        record["error"] = str(err)
        return None, record
    data = path.read_bytes()
    record["zip_sha256"] = fl.sha256_bytes(data)
    record["sha256_as_read_on_10_november"] = record["zip_sha256"] == ARCHIVE_SHA256
    record["vintage_line"] = fl._vintage_line(data)
    blocks = fl.parse_blocks(fl._csv_text(data))
    frame = blocks[0]["frame"] / 100.0
    return frame, record


def moments(f: pd.Series, start: str, end: str) -> dict:
    """Months, mean and standard deviation (per cent a year) and the annualised Sharpe ratio of f over
    the months start to end."""
    x = f.loc[start:end].dropna()
    return {"months": len(x), "mean": x.mean() * 1200, "sd": x.std() * np.sqrt(12) * 100,
            "sharpe": x.mean() / x.std() * np.sqrt(12)}
