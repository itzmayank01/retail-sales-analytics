#!/usr/bin/env python3
"""Make a slimmer Tableau upload file with only the columns the dashboard uses.

Same column names as retail_sales_tableau.csv, so existing calculated fields
keep working. Smaller file = faster upload and less risk of session timeout.

Output: tableau/retail_sales_tableau_slim.csv
Run:    .venv/bin/python scripts/slim_tableau_file.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tableau" / "retail_sales_tableau.csv"
OUT = ROOT / "tableau" / "retail_sales_tableau_slim.csv"

KEEP = ["RowType", "Invoice", "Date", "CustomerID", "Country",
        "Revenue", "ReturnValue", "Description", "Segment"]

df = pd.read_csv(SRC, usecols=KEEP, dtype={"Invoice": str})[KEEP]
df.to_csv(OUT, index=False)

s = df[df.RowType == "Sale"]
print(f"Rows: {len(df):,}")
print(f"Revenue: {s.Revenue.sum():,.2f}  (expected 19,327,626.52)")
print(f"Return value: {df.ReturnValue.sum():,.2f}  (expected 716,425.97)")
print(f"Size: {OUT.stat().st_size / 1e6:.1f} MB (was {SRC.stat().st_size / 1e6:.1f} MB)")
