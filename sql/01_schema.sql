-- Olist analytics schema (PostgreSQL)
DROP VIEW  IF EXISTS v_sales, v_orders;
DROP TABLE IF EXISTS payments, reviews, order_items, orders, products, sellers, customers CASCADE;

CREATE TABLE customers (
  customer_id        TEXT PRIMARY KEY,
  customer_unique_id TEXT NOT NULL,
  zip_prefix         INT,
  city               TEXT,
  state              CHAR(2)
);
CREATE TABLE sellers (
  seller_id  TEXT PRIMARY KEY,
  zip_prefix INT,
  city       TEXT,
  state      CHAR(2)
);
CREATE TABLE products (
  product_id           TEXT PRIMARY KEY,
  category_pt          TEXT,
  category             TEXT NOT NULL,          -- English, 'unknown' if missing
  name_length          INT,
  description_length   INT,
  photos_qty           INT,
  weight_g             NUMERIC,
  length_cm            NUMERIC,
  height_cm            NUMERIC,
  width_cm             NUMERIC
);
CREATE TABLE orders (
  order_id                      TEXT PRIMARY KEY,
  customer_id                   TEXT NOT NULL REFERENCES customers(customer_id),
  order_status                  TEXT NOT NULL,
  order_purchase_timestamp      TIMESTAMP NOT NULL,
  order_approved_at             TIMESTAMP,
  order_delivered_carrier_date  TIMESTAMP,
  order_delivered_customer_date TIMESTAMP,
  order_estimated_delivery_date TIMESTAMP,
  order_month                   DATE,
  is_delivered                  BOOLEAN,
  delivery_days                 NUMERIC(8,2),   -- NULL unless delivered
  delay_days                    NUMERIC(8,2),   -- >0 = later than promised
  late_flag                     SMALLINT        -- NULL unless delivered
);
CREATE TABLE order_items (
  order_id               TEXT NOT NULL REFERENCES orders(order_id),
  order_item_id          INT  NOT NULL,
  product_id             TEXT NOT NULL REFERENCES products(product_id),
  seller_id              TEXT NOT NULL REFERENCES sellers(seller_id),
  shipping_limit_date    TIMESTAMP,
  price                  NUMERIC(10,2) NOT NULL,
  freight_value          NUMERIC(10,2) NOT NULL,
  freight_to_price_ratio NUMERIC(10,4),
  PRIMARY KEY (order_id, order_item_id)
);
CREATE TABLE reviews (            -- one (latest) review per order
  order_id                TEXT PRIMARY KEY REFERENCES orders(order_id),
  review_id               TEXT,
  review_score            SMALLINT CHECK (review_score BETWEEN 1 AND 5),
  review_comment_title    TEXT,
  review_comment_message  TEXT,
  review_creation_date    TIMESTAMP,
  review_answer_timestamp TIMESTAMP
);
CREATE TABLE payments (
  order_id             TEXT NOT NULL REFERENCES orders(order_id),
  payment_sequential   INT  NOT NULL,
  payment_type         TEXT,
  payment_installments INT,
  payment_value        NUMERIC(10,2),
  PRIMARY KEY (order_id, payment_sequential)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_month    ON orders(order_month);
CREATE INDEX idx_items_seller    ON order_items(seller_id);
CREATE INDEX idx_items_product   ON order_items(product_id);
CREATE INDEX idx_cust_unique     ON customers(customer_unique_id);
