#!/usr/bin/env python3
"""Build one flat CSV for Tableau Public web authoring.

Web authoring is easiest with a single file, so this joins the star schema:
sales + returns rows (RowType = Sale / Return), with product name, price band
and customer RFM segment attached to every row.

Output: tableau/retail_sales_tableau.csv
Run:    .venv/bin/python scripts/build_tableau_file.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "data" / "clean"
OUT = ROOT / "tableau" / "retail_sales_tableau.csv"

txt = {"Invoice": str, "StockCode": str}
sales = pd.read_csv(C / "fact_sales.csv", dtype=txt)
rets = pd.read_csv(C / "fact_returns.csv", dtype=txt)
prod = pd.read_csv(C / "dim_product.csv", dtype=txt)[["StockCode", "Description", "PriceBand"]]
cust = pd.read_csv(C / "dim_customer.csv")[["CustomerID", "Segment"]]

sales = sales.assign(RowType="Sale", ReturnValue=0.0)
rets = rets.assign(RowType="Return", Revenue=0.0, Quantity=rets["Quantity"].abs(),
                   CustomerType=rets["CustomerID"].eq(0).map({True: "Guest", False: "Registered"}))

cols = ["RowType", "Invoice", "Date", "StockCode", "CustomerID", "CustomerType",
        "Country", "Quantity", "Revenue", "ReturnValue"]
flat = pd.concat([sales[cols], rets[cols]], ignore_index=True)
flat = flat.merge(prod, on="StockCode", how="left").merge(cust, on="CustomerID", how="left")
flat["Description"] = flat["Description"].fillna("UNKNOWN PRODUCT")
flat["Segment"] = flat["Segment"].fillna("Returns only")

OUT.parent.mkdir(parents=True, exist_ok=True)
flat.to_csv(OUT, index=False)

s = flat[flat.RowType == "Sale"]
print(f"Rows: {len(flat):,} (sales {len(s):,}, returns {(flat.RowType == 'Return').sum():,})")
print(f"Revenue: {s.Revenue.sum():,.2f}  (expected 19,327,626.52)")
print(f"Return value: {flat.ReturnValue.sum():,.2f}  (expected 716,425.97)")
print(f"File size: {OUT.stat().st_size / 1e6:.1f} MB")
