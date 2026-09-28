-- Item-grain sales fact: delivered orders only (revenue = item price, freight separate)
CREATE OR REPLACE VIEW v_sales AS
SELECT oi.order_id, oi.order_item_id, o.order_month, o.order_purchase_timestamp,
       c.customer_unique_id, c.state AS customer_state,
       oi.seller_id, s.state AS seller_state,
       p.category, oi.price, oi.freight_value, oi.freight_to_price_ratio,
       o.delivery_days, o.delay_days, o.late_flag, r.review_score
FROM order_items oi
JOIN orders    o ON o.order_id   = oi.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN products  p ON p.product_id  = oi.product_id
JOIN sellers   s ON s.seller_id   = oi.seller_id
LEFT JOIN reviews r ON r.order_id = oi.order_id
WHERE o.is_delivered;

-- Order-grain view: delivered orders, one row per order
CREATE OR REPLACE VIEW v_orders AS
SELECT o.order_id, o.order_month, o.order_purchase_timestamp, c.customer_unique_id, c.state AS customer_state,
       SUM(oi.price) AS revenue, SUM(oi.freight_value) AS freight, COUNT(*) AS n_items,
       o.delivery_days, o.delay_days, o.late_flag, r.review_score
FROM orders o
JOIN customers c   ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id  = o.order_id
LEFT JOIN reviews r ON r.order_id   = o.order_id
WHERE o.is_delivered
GROUP BY o.order_id, o.order_month, o.order_purchase_timestamp, c.customer_unique_id, c.state,
         o.delivery_days, o.delay_days, o.late_flag, r.review_score;
