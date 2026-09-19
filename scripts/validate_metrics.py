#!/usr/bin/env python3
"""Compute the key business metrics from the clean tables.

These numbers are the answer key: the Power BI dashboard must show the same
values, which proves the DAX measures are correct.

Run: .venv/bin/python scripts/validate_metrics.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "data" / "clean"

s = pd.read_csv(C / "fact_sales.csv", parse_dates=["InvoiceDate"])
r = pd.read_csv(C / "fact_returns.csv")
c = pd.read_csv(C / "dim_customer.csv")
p = pd.read_csv(C / "dim_product.csv")

rev = s.Revenue.sum()
orders = s.Invoice.nunique()
reg = c[c.CustomerID != 0]
out = []


def say(line=""):
    print(line)
    out.append(line)


say("# Key metrics (answer key for the Power BI dashboard)")
say()
say(f"- Total revenue: {rev:,.2f}")
say(f"- Orders: {orders:,}")
say(f"- Registered customers: {len(reg):,}")
say(f"- Average order value: {rev / orders:,.2f}")
say(f"- Units sold: {s.Quantity.sum():,}")
say(f"- Return value: {r.ReturnValue.sum():,.2f}")
say(f"- Return rate (by value): {r.ReturnValue.sum() / rev:.2%}")

s["Y"] = s.InvoiceDate.dt.year
s["M"] = s.InvoiceDate.dt.month
jn = lambda y: s[(s.Y == y) & (s.M <= 11)].Revenue.sum()
say(f"- Jan-Nov 2010: {jn(2010):,.0f} | Jan-Nov 2011: {jn(2011):,.0f} | "
    f"YoY growth (like-for-like): {jn(2011) / jn(2010) - 1:.1%}")

uk = s[s.Country == "United Kingdom"].Revenue.sum()
say(f"- UK share of revenue: {uk / rev:.1%}")
g = s[s.CustomerType == "Guest"].Revenue.sum()
say(f"- Guest (no customer ID) share of revenue: {g / rev:.1%}")
say(f"- Sep-Dec share of revenue: {s[s.M >= 9].Revenue.sum() / rev:.1%}")
m = s.groupby(["Y", "M"]).Revenue.sum()
say(f"- Peak month: {m.idxmax()[0]}-{m.idxmax()[1]:02d} ({m.max():,.0f})")
top10 = reg.Revenue.nlargest(int(len(reg) * 0.1)).sum() / reg.Revenue.sum()
say(f"- Top 10% of customers: {top10:.1%} of registered revenue")
say(f"- Repeat customers (2+ orders): {(reg.Orders > 1).mean():.1%}")

say()
say("## Top 5 countries outside the UK")
for k, v in s[s.Country != "United Kingdom"].groupby("Country").Revenue.sum().nlargest(5).items():
    say(f"- {k}: {v:,.0f}")

say()
say("## Revenue by weekday")
for k, v in s.groupby(s.InvoiceDate.dt.day_name()).Revenue.sum().sort_values(ascending=False).items():
    say(f"- {k}: {v:,.0f}")

say()
say("## Customer segments (RFM)")
seg = reg.groupby("Segment").agg(Customers=("CustomerID", "count"), Revenue=("Revenue", "sum"))
seg["Share"] = seg.Revenue / seg.Revenue.sum()
for k, row in seg.sort_values("Revenue", ascending=False).iterrows():
    say(f"- {k}: {int(row.Customers):,} customers, {row.Revenue:,.0f} revenue ({row.Share:.1%})")

say()
say("## Top 5 products by revenue")
top = (s.groupby("StockCode").Revenue.sum().nlargest(5).reset_index()
       .merge(p[["StockCode", "Description"]], on="StockCode"))
for _, row in top.iterrows():
    say(f"- {row.Description} ({row.StockCode}): {row.Revenue:,.0f}")

(ROOT / "reports" / "key_metrics.md").write_text("\n".join(out) + "\n")
