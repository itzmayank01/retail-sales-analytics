#!/usr/bin/env python3
"""Check the Excel workbook: sheet names, row counts and total revenue."""
from pathlib import Path

import pandas as pd

wb = Path(__file__).resolve().parent.parent / "powerbi" / "retail_sales_model.xlsx"
sheets = pd.read_excel(wb, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
for name, df in sheets.items():
    print(f"{name:<14} {len(df):>10,} rows")
print(f"Total revenue: {sheets['fact_sales']['Revenue'].sum():,.2f}  (expected 19,327,626.52)")
print(f"StockCode 85123A present: {(sheets['fact_sales']['StockCode'] == '85123A').any()}")
