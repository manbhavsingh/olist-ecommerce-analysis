import pandas as pd, numpy as np
R="data/raw/"; P="data/processed/"
orders=pd.read_csv(R+"olist_orders_dataset.csv")
items=pd.read_csv(R+"olist_order_items_dataset.csv")
cust=pd.read_csv(R+"olist_customers_dataset.csv")
prod=pd.read_csv(R+"olist_products_dataset.csv")
sell=pd.read_csv(R+"olist_sellers_dataset.csv")
rev=pd.read_csv(R+"olist_order_reviews_dataset.csv")
pay=pd.read_csv(R+"olist_order_payments_dataset.csv")
tr=pd.read_csv(R+"product_category_name_translation.csv")

# 1. timestamps
tcols=["order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]
for c in tcols: orders[c]=pd.to_datetime(orders[c])
items["shipping_limit_date"]=pd.to_datetime(items["shipping_limit_date"])
rev["review_creation_date"]=pd.to_datetime(rev["review_creation_date"])
rev["review_answer_timestamp"]=pd.to_datetime(rev["review_answer_timestamp"])

# 2. reviews: keep latest review per order
n0=len(rev)
rev=rev.sort_values(["order_id","review_answer_timestamp"]).drop_duplicates("order_id",keep="last")
print("reviews:",n0,"->",len(rev))

# 3. categories: translate, patch 2 missing translations, unknown for null
tr=pd.concat([tr,pd.DataFrame({"product_category_name":["pc_gamer","portateis_cozinha_e_preparadores_de_alimentos"],
                               "product_category_name_english":["pc_gamer","portable_kitchen_food_preparers"]})])
prod=prod.merge(tr,on="product_category_name",how="left")
prod["category"]=prod["product_category_name_english"].fillna("unknown")
print("products with unknown category:",(prod.category=="unknown").sum())
prod=prod.rename(columns={"product_name_lenght":"product_name_length","product_description_lenght":"product_description_length"})

# 4. order-level features
o=orders.copy()
o["order_month"]=o.order_purchase_timestamp.dt.to_period("M").dt.to_timestamp()
o["is_delivered"]=(o.order_status=="delivered")&o.order_delivered_customer_date.notna()
o["delivery_days"]=(o.order_delivered_customer_date-o.order_purchase_timestamp).dt.total_seconds()/86400
o["delay_days"]=(o.order_delivered_customer_date-o.order_estimated_delivery_date).dt.total_seconds()/86400
o["late_flag"]=np.where(o.is_delivered,(o.order_delivered_customer_date>o.order_estimated_delivery_date).astype(int),np.nan)
o.loc[~o.is_delivered,["delivery_days","delay_days"]]=np.nan
print("delivered w/ null delivery date:",((o.order_status=="delivered")&o.order_delivered_customer_date.isna()).sum())
print("negative delivery_days:",(o.delivery_days<0).sum())

# 5. item-level: freight ratio
items["freight_to_price_ratio"]=items.freight_value/items.price
print("items with price 0:",(items.price<=0).sum())

# 6. payments per order
payo=pay.groupby("order_id").agg(payment_value=("payment_value","sum"),payment_installments=("payment_installments","max"),
       payment_type=("payment_type",lambda s:s.value_counts().index[0])).reset_index()

# 7. order-level revenue (item price only, freight separate)
agg=items.groupby("order_id").agg(items_revenue=("price","sum"),freight=("freight_value","sum"),n_items=("order_item_id","count"),n_sellers=("seller_id","nunique")).reset_index()
o=o.merge(agg,on="order_id",how="left").merge(cust,on="customer_id",how="left").merge(rev[["order_id","review_score"]],on="order_id",how="left").merge(payo,on="order_id",how="left")
print("orders with no items:",o.items_revenue.isna().sum(), o[o.items_revenue.isna()].order_status.value_counts().to_dict())

# save
o.to_csv(P+"orders_clean.csv",index=False)
items.to_csv(P+"order_items_clean.csv",index=False)
prod.to_csv(P+"products_clean.csv",index=False)
sell.to_csv(P+"sellers_clean.csv",index=False)
cust.to_csv(P+"customers_clean.csv",index=False)
rev.to_csv(P+"reviews_clean.csv",index=False)
pay.to_csv(P+"payments_clean.csv",index=False)
print("saved. orders_clean",o.shape)
d=o[o.is_delivered]
print("delivered analysable:",len(d),"| late %:",round(d.late_flag.mean()*100,2),"| median delivery days:",round(d.delivery_days.median(),1),"| max:",round(d.delivery_days.max(),1))
print("delivered w/o review:",d.review_score.isna().sum())
