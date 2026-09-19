# Power BI Build Guide

Build the dashboard yourself, step by step. After each part, check the number
in **Verify** against `reports/key_metrics.md`. Matching numbers prove your
model and DAX are right.

Currency in this dataset is British pounds (GBP). Set currency formats to GBP.

---

## Part 0: If you use Power BI in the browser (Mac)

1. Go to app.powerbi.com and sign in with your UPES email.
   **Verify:** you see the Power BI home page (not an "account not allowed" error).
2. My workspace > New item > Semantic model > Excel (or Upload file) >
   choose `powerbi/retail_sales_model.xlsx` (one file, 5 sheets = 5 tables).
3. Tick all 5 tables and load.
   **Verify:** the semantic model lists fact_sales, fact_returns, dim_customer,
   dim_product and dim_date.
4. Open the semantic model > **Open data model** (web modelling). Do Part 2 and
   Part 3 there (relationships and measures work the same way).
5. Then Create report (blank) and build Parts 4 to 7.
6. Save the report as `Retail_Sales_Analytics`. Screenshots go in `screenshots/`.

If Power BI Desktop is available (Windows lab PC), skip Part 0 and follow Part 1.

---

## Part 1: Load the data

1. Open Power BI Desktop, then Home > Get data > Text/CSV.
2. Load these 5 files from `data/clean/`, one by one, clicking **Load** each time:
   `fact_sales.csv`, `fact_returns.csv`, `dim_customer.csv`, `dim_product.csv`, `dim_date.csv`
3. In Table view, check the column types:
   - `Date` columns: Date
   - `Revenue`, `Price`, `ReturnValue`, `AvgPrice`: Decimal number
   - `Quantity`, `CustomerID`, `Orders`: Whole number
   - `StockCode`, `Invoice`: Text (important: some codes like 85123A have letters)

**Verify:** fact_sales has 1,003,168 rows (shown bottom-left in Table view).

## Part 2: Build the star schema

In Model view, drag to create these relationships (all Many-to-one, single direction):

| From (many) | To (one) |
|---|---|
| fact_sales[Date] | dim_date[Date] |
| fact_sales[StockCode] | dim_product[StockCode] |
| fact_sales[CustomerID] | dim_customer[CustomerID] |
| fact_returns[Date] | dim_date[Date] |
| fact_returns[StockCode] | dim_product[StockCode] |

Then select dim_date > Table tools > **Mark as date table** > choose `Date`.
Sort `dim_date[Month]` by `MonthNum` (Column tools > Sort by column).

**Verify:** Model view shows fact tables in the middle, dimensions around them.

## Part 3: Create the measures

Open `powerbi/measures.dax`. Create each measure (Home > New measure).
Format: Revenue measures as GBP currency, 0 decimals. Percentages as %, 1 decimal.

**Verify:** drop `Total Revenue` in a Card: 19.33M. `Return Rate %`: 3.7%.

## Part 4: Page 1, Executive Overview

| Visual | Fields |
|---|---|
| Slicers (top) | dim_date[Year], dim_date[Quarter], fact_sales[Country] |
| 5 KPI cards | Total Revenue, Total Orders, Avg Order Value, Registered Customers, Return Rate % |
| Line chart | X: dim_date[YearMonth]; Y: Total Revenue |
| Clustered column | X: dim_date[Month]; Y: Total Revenue; Legend: dim_date[Year] |
| Bar chart | Y: fact_sales[Country]; X: Total Revenue; Top N filter = 10 |
| Card | UK Revenue Share % |

**Verify:** the line chart peaks at Nov 2011 (about 1.45M).
Set Year = 2011 and Month Jan to Nov in the filter pane: YoY Growth % is about 2.1%.

## Part 5: Page 2, Customer Analysis (RFM)

| Visual | Fields |
|---|---|
| Donut | Legend: dim_customer[Segment]; Values: Total Revenue |
| Clustered bar | Y: dim_customer[Segment]; X: count of CustomerID |
| Table | CustomerID, Country, Orders, Revenue, RecencyDays, Segment (top 20 by Revenue) |
| Cards | Repeat Customer %, Revenue per Customer, Guest Revenue Share % |
| Scatter | X: dim_customer[Orders]; Y: dim_customer[Revenue]; Legend: Segment |

**Verify:** Champions = 1,805 customers with about 77% of registered revenue.
Repeat Customer % = 72.3%. Guest Revenue Share % = 13.3%.

## Part 6: Page 3, Products and Returns

| Visual | Fields |
|---|---|
| Bar | Y: dim_product[Description]; X: Total Revenue; Top N = 10 |
| Column | X: dim_product[PriceBand]; Y: Total Revenue and Units Sold |
| Column | X: dim_date[Weekday] (sort by WeekdayNum); Y: Total Revenue |
| Line | X: dim_date[YearMonth]; Y: Return Value |
| Bar | Y: dim_product[Description]; X: Return Value; Top N = 10 |

**Verify:** top product = REGENCY CAKESTAND 3 TIER (about 331K).
Saturday revenue is almost zero (about 10K), which is a real insight (see README).

## Part 7: Polish

- One colour theme across pages (View > Themes).
- Title on every visual that states the insight, not just the metric
  (for example "Sep to Dec drives 46% of revenue", not "Revenue by month").
- Add page navigation buttons (Insert > Buttons > Navigator > Page navigator).
- Save as `powerbi/Retail_Sales_Analytics.pbix`.
- Export each page (File > Export > PDF, or a screenshot) into `screenshots/`.
