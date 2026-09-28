# SQL query notes (`03_analysis_queries.sql`)
All queries run on views `v_orders` (one row per delivered order) and `v_sales` (one row per delivered item). Revenue = item price, freight excluded.

| # | What it calculates | Why it matters | How to explain it |
|---|---|---|---|
| Q1 | Monthly revenue, orders, AOV (`GROUP BY order_month`) | Shows the growth trend and whether it comes from volume or basket size | Aggregate the order-level view by month; AOV = average revenue per order |
| Q2 | MoM revenue growth | Separates steady growth from seasonal spikes (Nov 2017 +52.4%) | A CTE builds monthly revenue; `LAG()` fetches last month; `NULLIF` avoids divide-by-zero |
| Q3 | Top 10 categories and revenue share | Shows concentration and where to focus | `SUM(SUM(price)) OVER ()` gives the grand total for each row's share |
| Q4 | Top 3 categories per state | Shows regional differences | `ROW_NUMBER() OVER (PARTITION BY state ORDER BY revenue DESC)`, then filter rn <= 3 |
| Q5 | Late % by state | Locates the delivery problem | `SUM(CASE WHEN late_flag=1 ...)/COUNT(*)`; `HAVING` >= 500 orders avoids noisy small states |
| Q6 | Seller ranking by revenue and lateness | Finds sellers where delivery performance and reviews differ | Aggregate to one seller-order row first, then use `RANK()` over sellers with 50+ orders; lateness/reviews are order-weighted |
| Q7 | Running revenue total | Shows cumulative growth | `SUM() OVER (ORDER BY month)`; the last row must equal total revenue (R$13,220,249) |
| Q8 | Repeat purchase rate | Measures loyalty | Group by `customer_unique_id` (not `customer_id`, which changes per order); count customers with more than 1 order |
| Q9 | Cohort retention | Shows how many customers come back by month | First order month per customer; month index via `age()`; active customers / cohort size |
| Q10 | Top 10% customers by spend | Measures revenue concentration | `NTILE(10)` over spend; decile 1 = 41.1% of revenue |
| Q11 | Order funnel | Shows where orders drop | `COUNT(DISTINCT order_id) FILTER (WHERE ...)` per stage |
| Q12 | Categories with 3 consecutive monthly declines | Early warning of weakening categories | `LAG` flags a decline; a 3-row window sums the flags; counts overlapping windows |
| Q13 | Median and P90 delivery time | Medians resist outliers (max is 209 days) | `PERCENTILE_CONT` with `ROLLUP` for the overall row; output keeps the overall row plus the seven highest-median states |
