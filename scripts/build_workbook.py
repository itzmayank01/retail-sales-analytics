#!/usr/bin/env python3
"""Package the 5 clean tables into one Excel workbook for Power BI upload.

Power BI in the browser (app.powerbi.com) accepts one Excel file and creates
one table per sheet, so a single upload loads the whole star schema.

Input : data/clean/*.csv
Output: powerbi/retail_sales_model.xlsx  (5 sheets)

Run: .venv/bin/python scripts/build_workbook.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "powerbi" / "retail_sales_model.xlsx"

TABLES = ["fact_sales", "fact_returns", "dim_customer", "dim_product", "dim_date"]
TEXT_COLS = {"Invoice": str, "StockCode": str}

with pd.ExcelWriter(OUT, engine="xlsxwriter") as xw:
    for name in TABLES:
        df = pd.read_csv(CLEAN / f"{name}.csv", dtype=TEXT_COLS)
        for col in ("Date", "InvoiceDate", "FirstPurchase", "LastPurchase"):
            if col in df:
                df[col] = pd.to_datetime(df[col])
        df.to_excel(xw, sheet_name=name, index=False)
        # Format as an Excel table so Power BI detects it cleanly
        ws = xw.sheets[name]
        ws.add_table(0, 0, len(df), len(df.columns) - 1, {
            "name": name,
            "columns": [{"header": c} for c in df.columns],
            "style": "Table Style Light 1",
        })
        print(f"{name:<14} {len(df):>10,} rows")

print(f"\nWrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
