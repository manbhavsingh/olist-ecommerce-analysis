-- Q1 Monthly revenue, orders, AOV
SELECT order_month, ROUND(SUM(revenue),0) AS revenue, COUNT(*) AS orders, ROUND(AVG(revenue),2) AS aov
FROM v_orders
GROUP BY order_month ORDER BY order_month;

-- Q2 Month-over-month revenue growth (CTE + LAG)
WITH m AS (
  SELECT order_month, SUM(revenue) AS revenue FROM v_orders GROUP BY order_month
)
SELECT order_month, ROUND(revenue,0) AS revenue,
       ROUND(100.0*(revenue - LAG(revenue) OVER (ORDER BY order_month))
             / NULLIF(LAG(revenue) OVER (ORDER BY order_month),0),1) AS mom_growth_pct
FROM m ORDER BY order_month;

-- Q3 Top 10 categories by revenue and share
SELECT category, ROUND(SUM(price),0) AS revenue,
       ROUND(100.0*SUM(price)/SUM(SUM(price)) OVER (),1) AS revenue_share_pct,
       COUNT(DISTINCT order_id) AS orders
FROM v_sales GROUP BY category ORDER BY revenue DESC LIMIT 10;

-- Q4 Top 3 categories per customer state (ROW_NUMBER)
WITH s AS (
  SELECT customer_state, category, SUM(price) AS revenue,
         ROW_NUMBER() OVER (PARTITION BY customer_state ORDER BY SUM(price) DESC) AS rn
  FROM v_sales GROUP BY customer_state, category
)
SELECT customer_state, rn, category, ROUND(revenue,0) AS revenue
FROM s WHERE rn <= 3 AND customer_state IN ('SP','RJ','MG','RS','BA') ORDER BY customer_state, rn;

-- Q5 Late delivery % by customer state (CASE WHEN)
SELECT customer_state, COUNT(*) AS delivered_orders,
       SUM(CASE WHEN late_flag = 1 THEN 1 ELSE 0 END) AS late_orders,
       ROUND(100.0*SUM(CASE WHEN late_flag = 1 THEN 1 ELSE 0 END)/COUNT(*),2) AS late_pct
FROM v_orders GROUP BY customer_state HAVING COUNT(*) >= 500 ORDER BY late_pct DESC;

-- Q6 Seller ranking (RANK): order-weighted lateness/reviews, sellers with 50+ orders
WITH seller_order AS (
  SELECT seller_id, seller_state, order_id,
         SUM(price) AS order_revenue,
         MAX(late_flag) AS late_flag,
         MAX(review_score) AS review_score
  FROM v_sales
  GROUP BY seller_id, seller_state, order_id
),
s AS (
  SELECT seller_id, seller_state, ROUND(SUM(order_revenue),0) AS revenue,
         COUNT(*) AS orders,
         ROUND(100.0*AVG(late_flag),1) AS late_pct,
         ROUND(AVG(review_score),2) AS avg_review
  FROM seller_order
  GROUP BY seller_id, seller_state
  HAVING COUNT(*) >= 50
)
SELECT seller_id, seller_state, revenue, orders, late_pct, avg_review,
       RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
       RANK() OVER (ORDER BY late_pct DESC) AS lateness_rank
FROM s ORDER BY late_pct DESC LIMIT 10;

-- Q7 Running (cumulative) revenue
WITH m AS (SELECT order_month, SUM(revenue) AS revenue FROM v_orders GROUP BY order_month)
SELECT order_month, ROUND(revenue,0) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY order_month),0) AS cumulative_revenue
FROM m ORDER BY order_month;

-- Q8 Repeat purchase rate (unique customers, GROUP BY + HAVING in a CTE)
WITH per_cust AS (
  SELECT customer_unique_id, COUNT(DISTINCT order_id) AS n_orders FROM v_orders GROUP BY customer_unique_id
), repeaters AS (
  SELECT customer_unique_id FROM per_cust WHERE n_orders > 1
)
SELECT (SELECT COUNT(*) FROM per_cust) AS customers,
       (SELECT COUNT(*) FROM repeaters) AS repeat_customers,
       ROUND(100.0*(SELECT COUNT(*) FROM repeaters)/(SELECT COUNT(*) FROM per_cust),2) AS repeat_rate_pct;

-- Q9 Cohort retention: first purchase month vs months since (share of cohort ordering again)
WITH first_order AS (
  SELECT customer_unique_id, MIN(order_month) AS cohort_month FROM v_orders GROUP BY customer_unique_id
), activity AS (
  SELECT DISTINCT v.customer_unique_id, f.cohort_month,
         (EXTRACT(YEAR FROM age(v.order_month, f.cohort_month))*12
          + EXTRACT(MONTH FROM age(v.order_month, f.cohort_month)))::INT AS month_n
  FROM v_orders v JOIN first_order f USING (customer_unique_id)
), sizes AS (SELECT cohort_month, COUNT(*) AS cohort_size FROM first_order GROUP BY cohort_month)
SELECT a.cohort_month, s.cohort_size, a.month_n,
       COUNT(DISTINCT a.customer_unique_id) AS active_customers,
       ROUND(100.0*COUNT(DISTINCT a.customer_unique_id)/s.cohort_size,2) AS retention_pct
FROM activity a JOIN sizes s USING (cohort_month)
WHERE a.month_n BETWEEN 0 AND 6 AND a.cohort_month BETWEEN '2017-01-01' AND '2018-02-01'
GROUP BY a.cohort_month, s.cohort_size, a.month_n ORDER BY a.cohort_month, a.month_n;

-- Q10 Top 10% customers by spend (NTILE)
WITH c AS (SELECT customer_unique_id, SUM(revenue) AS spend FROM v_orders GROUP BY customer_unique_id),
t AS (SELECT *, NTILE(10) OVER (ORDER BY spend DESC) AS decile FROM c)
SELECT decile, COUNT(*) AS customers, ROUND(SUM(spend),0) AS revenue,
       ROUND(100.0*SUM(spend)/SUM(SUM(spend)) OVER (),1) AS revenue_share_pct, ROUND(AVG(spend),0) AS avg_spend
FROM t GROUP BY decile ORDER BY decile;

-- Q11 Order funnel (COUNT DISTINCT + FILTER)
SELECT COUNT(DISTINCT order_id) AS placed,
       COUNT(DISTINCT order_id) FILTER (WHERE order_approved_at IS NOT NULL) AS approved,
       COUNT(DISTINCT order_id) FILTER (WHERE order_delivered_carrier_date IS NOT NULL) AS handed_to_carrier,
       COUNT(DISTINCT order_id) FILTER (WHERE order_delivered_customer_date IS NOT NULL) AS delivered,
       COUNT(DISTINCT order_id) FILTER (WHERE order_status IN ('canceled','unavailable')) AS canceled_or_unavailable
FROM orders;

-- Q12 Categories with 3 consecutive monthly revenue declines (Jan 2017 - Aug 2018)
WITH m AS (
  SELECT category, order_month, SUM(price) AS revenue FROM v_sales
  WHERE order_month BETWEEN '2017-01-01' AND '2018-08-01' GROUP BY category, order_month
), d AS (
  SELECT category, order_month, revenue,
         CASE WHEN revenue < LAG(revenue) OVER (PARTITION BY category ORDER BY order_month) THEN 1 ELSE 0 END AS declined,
         COUNT(*) OVER (PARTITION BY category) AS months_present
  FROM m
), r AS (
  SELECT *, SUM(declined) OVER (PARTITION BY category ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS declines_3m,
            COUNT(*) OVER (PARTITION BY category ORDER BY order_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS w
  FROM d WHERE months_present = 20
)
SELECT category, MIN(order_month) AS first_3_decline_window_end, COUNT(*) AS windows_with_3_declines
FROM r WHERE declines_3m = 3 AND w = 3 GROUP BY category ORDER BY windows_with_3_declines DESC LIMIT 10;

-- Q13 Median and P90 delivery time (PERCENTILE_CONT), overall and worst states
SELECT customer_state, COUNT(*) AS orders,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_days)::numeric,1) AS median_days,
       ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY delivery_days)::numeric,1) AS p90_days
FROM v_orders GROUP BY ROLLUP(customer_state) HAVING customer_state IS NULL OR COUNT(*) >= 500
ORDER BY (customer_state IS NOT NULL), median_days DESC LIMIT 8;
