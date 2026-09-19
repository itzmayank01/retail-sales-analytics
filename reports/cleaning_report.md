# Data Cleaning Report

Raw rows: **1,067,371**  |  Clean sales rows: **1,003,168**  |  Return rows: **17,914**

| Step | Rows before | Rows after | Reason |
|---|---:|---:|---|
| 1. Drop exact duplicate rows | 1,067,371 | 1,033,036 | Same invoice, product, qty, price and time recorded twice |
| 2. Remove non-product lines | 1,033,036 | 1,027,056 | Postage, bank charges, Amazon fees, manual adjustments, tests |
| 3. Split cancellations into returns table | 1,027,056 | 1,009,142 | 17,914 cancelled lines kept separately in fact_returns for return-rate analysis |
| 4. Remove zero/negative quantity or price | 1,009,142 | 1,003,214 | Stock write-offs and damaged-goods entries, not real sales |
| 5. Remove bulk orders (1,000+ units) cancelled in full | 1,003,214 | 1,003,168 | Mistaken bulk orders that would inflate revenue if kept |
| 6. Label missing Customer IDs as Guest | 1,003,168 | 1,003,168 | 226,637 lines kept for revenue totals (CustomerID = 0), excluded from customer analysis |

Top non-product codes removed:

| StockCode | Lines |
|---|---:|
| POST | 2,086 |
| DOT | 1,425 |
| M | 1,392 |
| C2 | 277 |
| D | 173 |
| S | 101 |
| BANK CHARGES | 100 |
| ADJUST | 67 |
| AMAZONFEE | 36 |
| DCGS0058 | 31 |

## Output tables (star schema)

- fact_sales: 1,003,168 rows
- fact_returns: 17,914 rows
- dim_customer: 5,853 rows (incl. 1 Guest row)
- dim_product: 4,706 rows
- dim_date: 739 rows
