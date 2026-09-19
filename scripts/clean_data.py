#!/usr/bin/env python3
"""Clean the UCI Online Retail II dataset and build a star schema for Power BI.

Input : data/raw/online_retail_raw.csv   (1,067,371 raw transaction lines)
Output: data/clean/fact_sales.csv, fact_returns.csv, dim_customer.csv,
        dim_product.csv, dim_date.csv, and reports/cleaning_report.md

Run:   .venv/bin/python scripts/clean_data.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "online_retail_raw.csv"
CLEAN = ROOT / "data" / "clean"
REPORT = ROOT / "reports" / "cleaning_report.md"

log = []  # (step, rows_before, rows_after, why)


def step(name, before, after, why):
    log.append((name, before, after, why))
    print(f"{name:<45} {before:>9,} -> {after:>9,}  ({before - after:,} removed)")


# ---------------------------------------------------------------- load
df = pd.read_csv(RAW, dtype={"Invoice": str, "StockCode": str})
df = df.rename(columns={"Customer ID": "CustomerID"})
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
raw_rows = len(df)
print(f"Loaded {raw_rows:,} raw rows\n")

# ---------------------------------------------------------------- 1. duplicates
n = len(df)
df = df.drop_duplicates()
step("1. Drop exact duplicate rows", n, len(df), "Same invoice, product, qty, price and time recorded twice")

# ---------------------------------------------------------------- text cleanup
df["Description"] = df["Description"].str.strip().str.upper()
df["StockCode"] = df["StockCode"].str.strip().str.upper()
df["Country"] = df["Country"].str.strip().replace({"EIRE": "Ireland", "RSA": "South Africa",
                                                   "Unspecified": "Unknown"})

# ---------------------------------------------------------------- 2. non-product lines
is_product = df["StockCode"].str.match(r"^\d{5}[A-Z]{0,2}$")
n = len(df)
dropped_codes = df.loc[~is_product, "StockCode"].value_counts().head(10)
df = df[is_product]
step("2. Remove non-product lines", n, len(df), "Postage, bank charges, Amazon fees, manual adjustments, tests")

# ---------------------------------------------------------------- 3. split returns
is_cancel = df["Invoice"].str.startswith("C")
returns = df[is_cancel].copy()
sales = df[~is_cancel].copy()
log.append(("3. Split cancellations into returns table", len(df), len(sales),
            f"{len(returns):,} cancelled lines kept separately in fact_returns for return-rate analysis"))
print(f"{'3. Split cancellations -> fact_returns':<45} {len(returns):,} return lines")

# ---------------------------------------------------------------- 4. invalid qty / price
n = len(sales)
sales = sales[(sales["Quantity"] > 0) & (sales["Price"] > 0)]
step("4. Remove zero/negative quantity or price", n, len(sales), "Stock write-offs and damaged-goods entries, not real sales")

# ---------------------------------------------------------------- 5. bulk orders cancelled in full
# e.g. a single 80,995-unit order that was cancelled minutes later
big_ret = returns.assign(Qty=returns["Quantity"].abs())[["CustomerID", "StockCode", "Qty"]]
big_ret = big_ret[big_ret["Qty"] >= 1000].drop_duplicates()
n = len(sales)
m = sales.merge(big_ret, left_on=["CustomerID", "StockCode", "Quantity"],
                right_on=["CustomerID", "StockCode", "Qty"], how="left", indicator=True)
sales = m[m["_merge"] == "left_only"].drop(columns=["Qty", "_merge"])
step("5. Remove bulk orders (1,000+ units) cancelled in full", n, len(sales),
     "Mistaken bulk orders that would inflate revenue if kept")

# ---------------------------------------------------------------- 6. missing customers
guest = sales["CustomerID"].isna()
sales["CustomerID"] = sales["CustomerID"].fillna(0).astype(int)
returns["CustomerID"] = returns["CustomerID"].fillna(0).astype(int)
sales["CustomerType"] = guest.map({True: "Guest", False: "Registered"})
log.append(("6. Label missing Customer IDs as Guest", len(sales), len(sales),
            f"{guest.sum():,} lines kept for revenue totals (CustomerID = 0), excluded from customer analysis"))
print(f"{'6. Label missing Customer IDs as Guest':<45} {guest.sum():,} guest lines kept")

# ---------------------------------------------------------------- derived columns
sales["Revenue"] = (sales["Quantity"] * sales["Price"]).round(2)
returns["ReturnValue"] = (returns["Quantity"].abs() * returns["Price"]).round(2)
for t in (sales, returns):
    t["Date"] = t["InvoiceDate"].dt.date

# ---------------------------------------------------------------- dimensions
dim_product = (sales.sort_values("InvoiceDate")
               .groupby("StockCode")
               .agg(Description=("Description", "last"), AvgPrice=("Price", "median"))
               .reset_index())
dim_product["PriceBand"] = pd.cut(dim_product["AvgPrice"], [0, 2, 5, 10, 1e9],
                                  labels=["Under 2", "2-5", "5-10", "10+"])

# RFM segmentation for registered customers
reg = sales[sales["CustomerID"] != 0]
snapshot = sales["InvoiceDate"].max() + pd.Timedelta(days=1)
rfm = reg.groupby("CustomerID").agg(
    Country=("Country", "last"),
    FirstPurchase=("InvoiceDate", "min"),
    LastPurchase=("InvoiceDate", "max"),
    Orders=("Invoice", "nunique"),
    Revenue=("Revenue", "sum"),
).reset_index()
rfm["RecencyDays"] = (snapshot - rfm["LastPurchase"]).dt.days
rfm["R"] = pd.qcut(rfm["RecencyDays"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["Orders"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["M"] = pd.qcut(rfm["Revenue"], 4, labels=[1, 2, 3, 4]).astype(int)


def segment(r):
    if r.R >= 3 and r.F >= 3 and r.M >= 3:
        return "Champions"
    if r.F >= 3:
        return "Loyal"
    if r.R >= 3:
        return "Recent / Promising"
    if r.R <= 1 and r.F >= 2:
        return "At Risk"
    return "Hibernating"


rfm["Segment"] = rfm.apply(segment, axis=1)
rfm["Revenue"] = rfm["Revenue"].round(2)
dim_customer = rfm[["CustomerID", "Country", "FirstPurchase", "LastPurchase",
                    "Orders", "Revenue", "RecencyDays", "R", "F", "M", "Segment"]]
guest_row = pd.DataFrame([{"CustomerID": 0, "Country": "Unknown", "Segment": "Guest"}])
dim_customer = pd.concat([dim_customer, guest_row], ignore_index=True)

dates = pd.date_range(sales["InvoiceDate"].min().normalize(), sales["InvoiceDate"].max().normalize())
dim_date = pd.DataFrame({"Date": dates.date})
dim_date["Year"] = dates.year
dim_date["Quarter"] = "Q" + dates.quarter.astype(str)
dim_date["MonthNum"] = dates.month
dim_date["Month"] = dates.strftime("%b")
dim_date["YearMonth"] = dates.strftime("%Y-%m")
dim_date["Weekday"] = dates.strftime("%a")
dim_date["WeekdayNum"] = dates.weekday + 1

# ---------------------------------------------------------------- write
CLEAN.mkdir(parents=True, exist_ok=True)
fact_cols = ["Invoice", "Date", "InvoiceDate", "StockCode", "CustomerID", "CustomerType",
             "Country", "Quantity", "Price", "Revenue"]
sales[fact_cols].to_csv(CLEAN / "fact_sales.csv", index=False)
returns[["Invoice", "Date", "StockCode", "CustomerID", "Country", "Quantity", "Price",
         "ReturnValue"]].to_csv(CLEAN / "fact_returns.csv", index=False)
dim_product.to_csv(CLEAN / "dim_product.csv", index=False)
dim_customer.to_csv(CLEAN / "dim_customer.csv", index=False)
dim_date.to_csv(CLEAN / "dim_date.csv", index=False)

# ---------------------------------------------------------------- report
REPORT.parent.mkdir(parents=True, exist_ok=True)
lines = ["# Data Cleaning Report", "",
         f"Raw rows: **{raw_rows:,}**  |  Clean sales rows: **{len(sales):,}**  |  "
         f"Return rows: **{len(returns):,}**", "",
         "| Step | Rows before | Rows after | Reason |", "|---|---:|---:|---|"]
lines += [f"| {s} | {b:,} | {a:,} | {w} |" for s, b, a, w in log]
lines += ["", "Top non-product codes removed:", "",
          "| StockCode | Lines |", "|---|---:|"]
lines += [f"| {k} | {v:,} |" for k, v in dropped_codes.items()]
lines += ["", "## Output tables (star schema)", "",
          f"- fact_sales: {len(sales):,} rows",
          f"- fact_returns: {len(returns):,} rows",
          f"- dim_customer: {len(dim_customer):,} rows (incl. 1 Guest row)",
          f"- dim_product: {len(dim_product):,} rows",
          f"- dim_date: {len(dim_date):,} rows"]
REPORT.write_text("\n".join(lines) + "\n")
print(f"\nWrote clean tables to {CLEAN} and report to {REPORT}")
