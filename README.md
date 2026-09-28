# Olist E-Commerce: Delivery Performance & Revenue Analysis
End-to-end data analysis of ~100K Brazilian e-commerce orders using **PostgreSQL, Python (pandas, SciPy) and Power BI**, ending in business recommendations.

## Business Problem
A marketplace wants to know where revenue comes from, where deliveries fail, whether late delivery hurts reviews and repeat purchasing, and what to do about it.
Story: Growth -> Revenue drivers -> Operational leakage -> Customer impact -> Recommendations.

## Objectives
Quantify growth drivers and concentration; locate delivery delays by state and seller; test associations between delivery delays, reviews and repeat purchase; recommend actions.

## Dataset
Olist Brazilian E-Commerce Public Dataset (Kaggle, `olistbr/brazilian-ecommerce`), 9 CSVs, 99,441 orders, Sep 2016 - Oct 2018. Not committed; see `data/README.md`.
Analysis window for trends: Jan 2017 - Aug 2018 (other months have very few orders). Currency: BRL.

## Tech Stack
PostgreSQL 16 (via `pgserver`), Python (pandas, NumPy, Matplotlib, Seaborn, SciPy, statsmodels), Power BI (report layout and DAX defined in `dashboard/`).

## Data Pipeline
Raw CSVs -> `src/clean.py` (cleaning + features) -> `data/processed/` -> `src/run_pg.py` (schema, load, views) -> SQL analysis -> notebook (EDA + statistics) -> `data/powerbi/` -> Power BI.
Key cleaning decisions (problem -> decision -> reason):
- 547 orders have multiple reviews -> keep the latest review -> one score per order, no review-join duplication
- `customer_id` is new per order -> use `customer_unique_id` -> otherwise repeat rate is meaningless
- 610 products with no category -> label `unknown`, no imputation
- Undelivered orders have no delivery date -> delay metrics for the 96,470 delivered orders only
- Revenue analysis is restricted to delivered orders; non-delivered orders are therefore excluded from revenue
- Late = delivered date after estimated date; revenue = item price (freight separate)
Validation: order-level and item-level views both sum to R$13,220,248.93.

## SQL Analysis
13 queries in `sql/03_analysis_queries.sql` (explanations in `sql/README.md`): monthly revenue, MoM growth (LAG), top categories, top categories per state (ROW_NUMBER), late % (CASE WHEN), seller ranking (RANK), running total, repeat rate, cohort retention, NTILE deciles, funnel, consecutive declines, median delivery (PERCENTILE_CONT).

## Python Analysis
`notebooks/olist_analysis.ipynb`: quality checks, feature engineering (delivery_days, delay_days, late_flag, order_month, freight_to_price_ratio), 9 charts in `reports/figures/`.

## Statistical Analysis
| Test | Result |
|---|---|
| Mann-Whitney U: reviews late vs on-time | mean 2.57 vs 4.29; 1-star 46.2% vs 6.6%; p < 0.001; rank-biserial r = -0.55 |
| Chi-square: late first order vs repeat purchase | 3.18% vs 4.04%; chi2 = 7.89, p = 0.005 (small effect) |
| Wilson 95% CI: late rate | 8.11% (7.94% - 8.29%) |

## Power BI Dashboard
3 pages: Executive Summary, Sales & Customers, Logistics & Experience.
The dashboard tables are in `data/powerbi/`; `dashboard/README.md` has the model, DAX measures and the exact values the KPI cards must show. `dashboard/preview_page*.png` are Python-rendered previews of the layout (`src/dashboard_preview.py`), not Power BI exports.

## Key Findings
- Jan-Aug 2018 vs 2017: revenue +141.1%, orders +139.9%, AOV +0.5%: growth is volume, then plateaued after Mar 2018.
- SP+RJ+MG = 63.4% of revenue; top 10% of customers = 41.1%; top 10% of sellers = 67.1%.
- Only 3.0% of customers reorder; month-1 cohort retention averages 0.47%.
- 8.11% of orders late; MA 19.7%, CE 15.3%, BA 14.0%, RJ 13.5% vs SP 5.9%; these four states = 31.4% of late orders.
- Reviews are lower for late orders and decline across delay buckets: 4.29 on-time to 1.73 for 7+ days late.

## Business Recommendations
See `reports/business_playbook.md`: fix delivery in RJ/BA/MA/CE, set state-specific promise dates, review 31 high-late sellers, launch a retention program.

## Project Structure
```
olist-data-analysis/
  data/ (README only; raw/processed/powerbi are generated)
  notebooks/olist_analysis.ipynb, olist_analysis.py
  sql/01_schema.sql, 02_clean_view.sql, 03_analysis_queries.sql, README.md
  src/clean.py, load_postgres.py, run_pg.py, run_queries.py
  dashboard/README.md (+ .pbix and screenshots)
  reports/business_playbook.md, figures/
  requirements.txt
```

## How to Run
```bash
pip install -r requirements.txt
# put the 9 Olist CSVs in data/raw/
python src/clean.py
python src/run_pg.py            # starts PostgreSQL, loads tables, creates views
python src/run_queries.py Q5    # run one query (or none = all)
jupyter nbconvert --to notebook --execute --inplace notebooks/olist_analysis.ipynb
```
Expected: row counts 99441 / 3095 / 32951 / 99441 / 112650 / 98673 / 103886 and revenue 13220248.93.

## Skills Demonstrated
Analytical SQL (CTEs, window functions, cohorts), data cleaning, pandas EDA, hypothesis testing (Mann-Whitney, chi-square, confidence intervals), Power BI/DAX, business recommendations.

## Limitations
Associations, not causal claims; tests do not control for state, category or seller; seller lateness/review rates are weighted by distinct seller-order pairs; repeated customers may introduce dependence; one marketplace, 2016-2018.
