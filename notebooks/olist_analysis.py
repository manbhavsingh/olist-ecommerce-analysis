# %% [markdown]
# # Olist E-Commerce: Delivery Performance & Revenue Analysis
# **Business problem:** where does revenue come from, where do deliveries fail, and does it hurt reviews and repeat purchases?
# **Story:** Growth -> Revenue drivers -> Operational leakage -> Customer impact -> Recommendations
# Run `python src/clean.py` first (creates data/processed/). Revenue = item price of delivered orders (BRL), freight excluded.

# %%
import os, numpy as np, pandas as pd, matplotlib
import matplotlib.pyplot as plt, seaborn as sns
from scipy import stats
from statsmodels.stats.proportion import proportion_confint
if os.getcwd().endswith("notebooks"): os.chdir("..")
os.makedirs("reports/figures", exist_ok=True)
sns.set_theme(style="whitegrid"); plt.rcParams["figure.dpi"]=110
def save(name): plt.tight_layout(); plt.savefig(f"reports/figures/{name}.png"); plt.show()

# %% [markdown]
# ## 1. Data loading and quality checks (raw files)
# %%
R="data/raw/"
raw={n:pd.read_csv(R+f) for n,f in {"orders":"olist_orders_dataset.csv","items":"olist_order_items_dataset.csv","reviews":"olist_order_reviews_dataset.csv",
     "customers":"olist_customers_dataset.csv","products":"olist_products_dataset.csv","sellers":"olist_sellers_dataset.csv","payments":"olist_order_payments_dataset.csv"}.items()}
for n,df in raw.items():
    nl=df.isnull().sum(); print(f"{n:10s} shape={df.shape} duplicate_rows={df.duplicated().sum()} nulls={nl[nl>0].to_dict()}")
print(raw["orders"].order_status.value_counts())
print("reviews: orders with >1 review =",(raw["reviews"].groupby("order_id").size()>1).sum())
print("customer_id vs customer_unique_id:",raw["customers"].customer_id.nunique(),raw["customers"].customer_unique_id.nunique())

# %% [markdown]
# ## 2. Cleaning decisions (Problem -> Decision -> Reason) are implemented in `src/clean.py`
# - Multiple reviews per order -> keep latest -> one score per order, no join duplication
# - `customer_id` changes per order -> use `customer_unique_id` for repeat/cohort -> otherwise repeat rate is ~0
# - Null category (610 products) -> label `unknown`, no imputation
# - Undelivered orders have no delivery date -> delay metrics only for delivered orders
# - Canceled/unavailable orders have no items -> excluded from revenue
# %%
o=pd.read_csv("data/processed/orders_clean.csv",parse_dates=["order_month","order_purchase_timestamp"])
items=pd.read_csv("data/processed/order_items_clean.csv")
prod=pd.read_csv("data/processed/products_clean.csv"); sell=pd.read_csv("data/processed/sellers_clean.csv")
d=o[o.is_delivered].copy(); d["revenue"]=d.items_revenue
print("delivered orders:",len(d)," revenue:",round(d.revenue.sum(),2))
# Feature check: delivery_days, delay_days, late_flag, order_month, freight_to_price_ratio (item level)
print(d[["delivery_days","delay_days","late_flag"]].describe().round(2))
print("freight_to_price_ratio median:",round(items.freight_to_price_ratio.median(),3))
win=d[(d.order_month>="2017-01-01")&(d.order_month<="2018-08-01")]   # reliable window

# %% [markdown]
# ## 3. Growth: monthly revenue and orders
# %%
m=win.groupby("order_month").agg(revenue=("revenue","sum"),orders=("order_id","count"),aov=("revenue","mean"))
fig,ax=plt.subplots(figsize=(10,4)); ax.plot(m.index,m.revenue/1e3,marker="o",color="#1f77b4"); ax.set_ylabel("Revenue (R$ thousand)")
ax2=ax.twinx(); ax2.bar(m.index,m.orders,width=20,alpha=.2,color="grey"); ax2.set_ylabel("Orders"); ax.set_title("Monthly revenue and orders (Jan 2017 - Aug 2018)")
save("01_monthly_revenue_orders")
a=win[win.order_month<="2017-08-01"]; b=win[win.order_month>="2018-01-01"]
print(f"Jan-Aug YoY: revenue {b.revenue.sum()/a.revenue.sum()-1:+.1%}, orders {len(b)/len(a)-1:+.1%}, AOV {b.revenue.mean()/a.revenue.mean()-1:+.1%} (R${a.revenue.mean():.2f} -> R${b.revenue.mean():.2f})")

# %% [markdown]
# ## 4. Revenue drivers: categories and states
# %%
s=items.merge(d[["order_id","customer_state"]],on="order_id").merge(prod[["product_id","category"]],on="product_id")
cat=s.groupby("category").price.sum().sort_values(ascending=False); share=cat/cat.sum()*100
fig,ax=plt.subplots(figsize=(8,4.5)); sns.barplot(x=cat.head(10)/1e3,y=cat.head(10).index,color="#1f77b4",ax=ax); ax.set_xlabel("Revenue (R$ thousand)"); ax.set_title("Top 10 categories by revenue")
save("02_top_categories"); print("top-5 category share %:",round(share.head(5).sum(),1),"| top-10:",round(share.head(10).sum(),1))
st=d.groupby("customer_state").agg(revenue=("revenue","sum"),orders=("order_id","count")).sort_values("revenue",ascending=False)
st["share"]=st.revenue/st.revenue.sum()*100
fig,ax=plt.subplots(figsize=(8,4.5)); sns.barplot(x=st.head(10).revenue/1e3,y=st.head(10).index,color="#2a9d8f",ax=ax); ax.set_xlabel("Revenue (R$ thousand)"); ax.set_title("Top 10 states by revenue")
save("03_top_states"); print(st.head(5).round(1)); print("SP+RJ+MG share %:",round(st.loc[["SP","RJ","MG"],"share"].sum(),1))

# %% [markdown]
# ## 5. Operational leakage: delivery time and lateness
# %%
fig,ax=plt.subplots(figsize=(8,4)); sns.histplot(d.delivery_days.clip(upper=60),bins=60,color="#e76f51",ax=ax)
ax.axvline(d.delivery_days.median(),color="k",ls="--"); ax.set_xlabel("Delivery days (clipped at 60)"); ax.set_title("Delivery time distribution")
save("04_delivery_time_hist")
print("median",round(d.delivery_days.median(),1),"p90",round(d.delivery_days.quantile(.9),1),"p99",round(d.delivery_days.quantile(.99),1),"| >30 days:",round((d.delivery_days>30).mean()*100,2),"%")
print("estimated-vs-actual: median promised days",round(((pd.to_datetime(o.loc[d.index,'order_estimated_delivery_date'])-d.order_purchase_timestamp).dt.days).median(),1))
ls=d.groupby("customer_state").agg(orders=("order_id","count"),late_pct=("late_flag",lambda x:x.mean()*100),late_orders=("late_flag","sum"),median_days=("delivery_days","median"))
ls=ls[ls.orders>=500].sort_values("late_pct",ascending=False); overall=d.late_flag.mean()*100
fig,ax=plt.subplots(figsize=(8,5)); sns.barplot(x=ls.late_pct,y=ls.index,color="#e76f51",ax=ax); ax.axvline(overall,color="k",ls="--"); ax.set_xlabel("Late delivery %"); ax.set_title(f"Late delivery % by state (dashed = overall {overall:.1f}%)")
save("05_late_pct_by_state"); print(ls.round(2).head(6))
excess=(ls.late_orders-ls.orders*ls.loc["SP","late_pct"]/100).clip(lower=0).sort_values(ascending=False)
print("excess late orders vs SP-rate benchmark (top 5):\n",excess.head(5).round(0)); print("share of all late orders from RJ+BA+MA+CE:",round(ls.loc[["RJ","BA","MA","CE"],"late_orders"].sum()/d.late_flag.sum()*100,1),"%")

# %% [markdown]
# ## 6. Sellers
# %%
sd=items.merge(d[["order_id","late_flag","review_score"]],on="order_id")
seller_order=sd.groupby(["seller_id","seller_state","order_id"],as_index=False).agg(revenue=("price","sum"),late_flag=("late_flag","first"),review_score=("review_score","first"))
sp=seller_order.groupby(["seller_id","seller_state"]).agg(orders=("order_id","nunique"),revenue=("revenue","sum"),late_pct=("late_flag",lambda x:x.mean()*100),avg_review=("review_score","mean")).query("orders>=50")
fig,ax=plt.subplots(figsize=(7,5)); ax.scatter(sp.late_pct,sp.avg_review,s=sp.revenue/1500,alpha=.4,color="#264653"); ax.set_xlabel("Late %"); ax.set_ylabel("Avg review"); ax.set_title("Sellers with 50+ orders (bubble = revenue)")
save("06_seller_late_vs_review")
print("sellers 50+ orders:",len(sp),"| corr(late%,avg review)=",round(sp.late_pct.corr(sp.avg_review),2),"| sellers >15% late:",(sp.late_pct>15).sum(),"with revenue share of these 50+ sellers %:",round(sp[sp.late_pct>15].revenue.sum()/sp.revenue.sum()*100,1))
print("top 10% sellers share of seller revenue % (all sellers):",round(seller_order.groupby('seller_id').revenue.sum().sort_values(ascending=False).head(int(seller_order.seller_id.nunique()*.1)).sum()/seller_order.revenue.sum()*100,1))

# %% [markdown]
# ## 7. Customer impact: reviews and repeat purchase (with statistics)
# %%
r=d.dropna(subset=["review_score"]); late=r[r.late_flag==1].review_score; ont=r[r.late_flag==0].review_score
dist=r.groupby("late_flag").review_score.value_counts(normalize=True).unstack()*100
dist.index=["On-time","Late"]; dist.plot(kind="bar",stacked=True,figsize=(6,4),colormap="RdYlGn"); plt.ylabel("% of orders"); plt.title("Review score mix: on-time vs late"); plt.legend(title="Score",bbox_to_anchor=(1,1)); plt.xticks(rotation=0)
save("07_review_by_lateness")
d["bucket"]=pd.cut(d.delay_days,[-1000,-1e-4,3,7,1000],labels=["On-time","1-3d late","3-7d late","7+d late"])
bk=d.dropna(subset=["review_score"]).groupby("bucket",observed=True).review_score.agg(["count","mean"]).round(2)
fig,ax=plt.subplots(figsize=(6,4)); sns.barplot(x=bk.index,y=bk["mean"],color="#e9c46a",ax=ax); ax.set_ylabel("Avg review score"); ax.set_title("Avg review by delay bucket")
save("08_review_by_delay_bucket"); print(bk)
# Stat 1: Mann-Whitney U (ordinal, skewed 1-5 scores -> no normality assumption)
u=stats.mannwhitneyu(late,ont,alternative="two-sided"); auc=u.statistic/(len(late)*len(ont))
print(f"STAT1 Mann-Whitney U={u.statistic:,.0f}, p={u.pvalue:.3g} (p<1e-300 means underflow, i.e. effectively 0); n_late={len(late):,}, n_ontime={len(ont):,}")
print(f"means late {late.mean():.2f} vs on-time {ont.mean():.2f}; medians {late.median()} vs {ont.median()}; rank-biserial r={2*auc-1:.2f}; 1-star: {(late==1).mean():.1%} vs {(ont==1).mean():.1%}")
# Stat 2: chi-square, first-order lateness vs later repeat purchase (customers with >=180 days of follow-up)
d2=d.sort_values("order_purchase_timestamp"); cnt=d2.groupby("customer_unique_id").size()
first=d2.groupby("customer_unique_id").head(1).set_index("customer_unique_id")
coh=first[first.order_purchase_timestamp<=d2.order_purchase_timestamp.max()-pd.Timedelta(days=180)].copy(); coh["repeat"]=(cnt.reindex(coh.index)>1).astype(int)
ct=pd.crosstab(coh.late_flag,coh["repeat"]); chi=stats.chi2_contingency(ct,correction=False)
print("STAT2 contingency (rows late_flag 0/1, cols repeat 0/1):\n",ct); print(f"chi2={chi[0]:.2f}, dof={chi[2]}, p={chi[1]:.4f}; repeat rate on-time first order {coh[coh.late_flag==0]['repeat'].mean():.2%} vs late {coh[coh.late_flag==1]['repeat'].mean():.2%}")
# Stat 3: Wilson 95% CI for late rate
k,n=int(d.late_flag.sum()),len(d); lo,hi=proportion_confint(k,n,method="wilson"); print(f"STAT3 late rate {k/n:.2%} (95% CI {lo:.2%} - {hi:.2%}), {k:,} of {n:,}")

# %% [markdown]
# ## 8. Repeat purchase and cohort retention
# %%
per=d.groupby("customer_unique_id").order_id.nunique(); print(f"customers {len(per):,}; repeat {int((per>1).sum()):,} = {(per>1).mean():.2%}; max orders by one customer {per.max()}")
d["cohort"]=d.groupby("customer_unique_id").order_month.transform("min")
d["month_n"]=((d.order_month.dt.year-d.cohort.dt.year)*12+(d.order_month.dt.month-d.cohort.dt.month))
act=d.groupby(["cohort","month_n"]).customer_unique_id.nunique().reset_index(name="active")
size=d.groupby("cohort").customer_unique_id.nunique().rename("size"); act=act.join(size,on="cohort"); act["ret"]=act.active/act["size"]*100
hm=act[(act.cohort>="2017-01-01")&(act.cohort<="2018-02-01")&(act.month_n.between(1,6))].pivot(index="cohort",columns="month_n",values="ret")
hm.index=hm.index.strftime("%Y-%m")
fig,ax=plt.subplots(figsize=(7,5)); sns.heatmap(hm,annot=True,fmt=".2f",cmap="Blues",ax=ax); ax.set_title("Cohort retention % (months 1-6 after first purchase)")
save("09_cohort_retention"); print("avg month-1 retention over cohorts %:",round(hm[1].mean(),2),"| max cell %:",round(hm.max().max(),2))
newrep=d.assign(is_first=d.order_month==d.cohort).groupby("order_month").is_first.mean()
print("share of monthly orders from returning customers (mean Jan17-Aug18) %:",round((1-newrep.loc['2017-01-01':'2018-08-01']).mean()*100,1))

# %% [markdown]
# ## 9. Export tables for Power BI
# %%
os.makedirs("data/powerbi",exist_ok=True)
d["customer_type_first"]=np.where(d.order_month==d.cohort,"New","Returning")
d[["order_id","order_purchase_timestamp","order_month","customer_unique_id","customer_state","revenue","freight","n_items","delivery_days","delay_days","late_flag","review_score","bucket","customer_type_first","cohort"]].to_csv("data/powerbi/orders.csv",index=False)
s2=items.merge(d[["order_id","order_month","customer_state","late_flag","review_score"]],on="order_id").merge(prod[["product_id","category"]],on="product_id").merge(sell[["seller_id","seller_state"]],on="seller_id")
s2[["order_id","order_item_id","order_month","customer_state","seller_id","seller_state","category","price","freight_value","late_flag","review_score"]].to_csv("data/powerbi/order_items.csv",index=False)
act[(act.month_n<=12)].to_csv("data/powerbi/cohort_retention.csv",index=False)
sp.reset_index().to_csv("data/powerbi/sellers_50plus.csv",index=False)
print("exported:",os.listdir("data/powerbi"))
