#!/usr/bin/env python3
"""Convert the raw UCI Online Retail II Excel file (2 sheets) into one CSV.

Input : data/raw/online_retail_II.xlsx
Output: data/raw/online_retail_raw.csv

Run: .venv/bin/python scripts/convert_raw.py
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

sheets = pd.read_excel(RAW / "online_retail_II.xlsx", sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)
df.to_csv(RAW / "online_retail_raw.csv", index=False)
print(f"Sheets: {list(sheets)} -> {len(df):,} rows written to online_retail_raw.csv")
