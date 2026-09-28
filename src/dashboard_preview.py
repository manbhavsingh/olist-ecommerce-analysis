# Renders the 3 dashboard pages as images from data/powerbi/*.csv (preview of the Power BI layout, NOT a Power BI export)
import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
sns.set_theme(style="white"); ACC="#1f77b4"; RED="#e76f51"
o=pd.read_csv("data/powerbi/orders.csv",parse_dates=["order_month"]); it=pd.read_csv("data/powerbi/order_items.csv",parse_dates=["order_month"])
co=pd.read_csv("data/powerbi/cohort_retention.csv",parse_dates=["cohort"]); sp=pd.read_csv("data/powerbi/sellers_50plus.csv")
K=dict(rev=o.revenue.sum(),n=len(o),aov=o.revenue.mean(),late=o.late_flag.mean()*100,rv=o.review_score.mean())
print("KPI",{k:round(v,2) for k,v in K.items()})
w=o[(o.order_month>="2017-01-01")&(o.order_month<="2018-08-01")]
def cards(fig,items):
    for i,(t,v) in enumerate(items):
        ax=fig.add_axes([0.03+i*0.19,0.82,0.17,0.10]); ax.axis("off"); ax.add_patch(plt.Rectangle((0,0),1,1,color="#f3f6fa",transform=ax.transAxes))
        ax.text(.5,.62,v,ha="center",va="center",fontsize=18,weight="bold",color="#222"); ax.text(.5,.2,t,ha="center",va="center",fontsize=9,color="#666")
def page(name,title,sub):
    fig=plt.figure(figsize=(14,8)); fig.text(0.03,0.985,title,va="top",fontsize=15,weight="bold"); fig.text(0.03,0.945,sub,va="top",fontsize=9.5,color="#555"); return fig
# Page 1
f=page(1,"Olist - Executive Summary","Growth came from order volume: AOV flat at ~R$136. Preview rendered in Python from the dashboard tables.")
cards(f,[("Total Revenue",f"R${K['rev']/1e6:.2f}M"),("Orders",f"{K['n']:,}"),("AOV",f"R${K['aov']:.2f}"),("Late Delivery %",f"{K['late']:.2f}%"),("Avg Review",f"{K['rv']:.2f}")])
m=w.groupby("order_month").revenue.sum()/1e3
a1=f.add_axes([0.05,0.47,0.9,0.31]); a1.plot(m.index,m.values,marker="o",color=ACC); a1.set_title("Monthly revenue (R$ thousand), Jan 2017 - Aug 2018",loc="left",fontsize=11); a1.grid(axis="y",alpha=.3)
st=o.groupby("customer_state").revenue.sum().sort_values(ascending=False).head(10)/1e3
a2=f.add_axes([0.08,0.06,0.38,0.32]); sns.barplot(x=st.values,y=st.index,color="#2a9d8f",ax=a2); a2.set_title("Revenue by state (top 10, R$ thousand)",loc="left",fontsize=11); a2.set_xlabel(""); a2.set_ylabel("")
ca=it.groupby("category").price.sum().sort_values(ascending=False).head(10)/1e3
a3=f.add_axes([0.70,0.06,0.27,0.32]); sns.barplot(x=ca.values,y=ca.index,color=ACC,ax=a3); a3.set_title("Top 10 categories (R$ thousand)",loc="left",fontsize=11); a3.set_xlabel(""); a3.set_ylabel("")
f.savefig("dashboard/preview_page1_executive_summary.png",dpi=110); plt.close(f)
# Page 2
f=page(2,"Olist - Sales & Customers","Only about 3% of customers ever reorder. Preview rendered in Python from the dashboard tables.")
per=o.groupby("customer_unique_id").order_id.nunique(); ret=(w.customer_type_first=="Returning").mean()*100
cards(f,[("Customers",f"{len(per):,}"),("Repeat customers",f"{int((per>1).sum()):,}"),("Repeat rate",f"{(per>1).mean()*100:.1f}%"),("Returning order share",f"{ret:.1f}%"),("Top-10% customer share","41.1%")])
nr=w.groupby(["order_month","customer_type_first"]).size().unstack(fill_value=0); nr.index=nr.index.strftime("%y-%m")
a1=f.add_axes([0.05,0.5,0.55,0.29]); nr.plot(kind="bar",stacked=True,ax=a1,color=[ "#e9c46a",ACC],width=.8); a1.tick_params(axis="x",rotation=60,labelsize=8); a1.set_title("Orders per month: New vs Returning customers",loc="left",fontsize=11); a1.set_xlabel(""); a1.legend(title="",fontsize=8)
hm=co[(co.cohort>="2017-01-01")&(co.cohort<="2018-02-01")&(co.month_n.between(1,6))].pivot(index="cohort",columns="month_n",values="ret"); hm.index=hm.index.strftime("%Y-%m")
a2=f.add_axes([0.70,0.45,0.27,0.34]); sns.heatmap(hm,annot=True,fmt=".2f",cmap="Blues",cbar=False,ax=a2,annot_kws={"size":6}); a2.set_title("Cohort retention % (months 1-6)",loc="left",fontsize=11); a2.set_ylabel(""); a2.set_xlabel("months since first purchase"); a2.tick_params(labelsize=7)
ca=it.groupby("category").price.sum().sort_values(ascending=False).head(8)/1e3
a3=f.add_axes([0.18,0.06,0.27,0.30]); sns.barplot(x=ca.values,y=ca.index,color=ACC,ax=a3); a3.set_title("Category revenue (R$ thousand)",loc="left",fontsize=11); a3.set_xlabel(""); a3.set_ylabel("")
st=o.groupby("customer_state").revenue.sum().sort_values(ascending=False).head(8)/1e3
a4=f.add_axes([0.62,0.06,0.33,0.30]); sns.barplot(x=st.values,y=st.index,color="#2a9d8f",ax=a4); a4.set_title("State revenue (R$ thousand)",loc="left",fontsize=11); a4.set_xlabel(""); a4.set_ylabel("")
f.savefig("dashboard/preview_page2_sales_customers.png",dpi=110); plt.close(f)
# Page 3
f=page(3,"Olist - Logistics & Experience","Review scores are lower in later-delivery buckets. Preview rendered in Python from the dashboard tables.")
cards(f,[("Late Delivery %",f"{K['late']:.2f}%"),("Late orders",f"{int(o.late_flag.sum()):,}"),("Median delivery days",f"{o.delivery_days.median():.1f}"),("P90 delivery days",f"{o.delivery_days.quantile(.9):.1f}"),("Avg review (late / on-time)",f"{o[o.late_flag==1].review_score.mean():.2f} / {o[o.late_flag==0].review_score.mean():.2f}")])
ls=o.groupby("customer_state").agg(n=("order_id","count"),lp=("late_flag",lambda x:x.mean()*100)).query("n>=500").sort_values("lp",ascending=False)
a1=f.add_axes([0.07,0.08,0.26,0.70]); sns.barplot(x=ls.lp,y=ls.index,color=RED,ax=a1); a1.axvline(K["late"],color="k",ls="--"); a1.set_title("Late % by state (dashed = overall)",loc="left",fontsize=11); a1.set_xlabel(""); a1.set_ylabel("")
order=["On-time","1-3d late","3-7d late","7+d late"]; bk=o.groupby("bucket").review_score.mean().reindex(order)
a2=f.add_axes([0.42,0.50,0.25,0.28]); sns.barplot(x=bk.index,y=bk.values,color="#e9c46a",ax=a2); a2.set_title("Avg review by delay bucket",loc="left",fontsize=11); a2.set_xlabel(""); a2.tick_params(labelsize=8)
band=pd.cut(o.delivery_days,[0,7,14,21,30,1000],labels=["0-7d","8-14d","15-21d","22-30d","30d+"]).value_counts().sort_index()
a3=f.add_axes([0.42,0.08,0.25,0.28]); sns.barplot(x=band.index,y=band.values,color=RED,ax=a3); a3.set_title("Delivery time distribution (orders)",loc="left",fontsize=11); a3.set_xlabel(""); a3.tick_params(labelsize=8)
a4=f.add_axes([0.75,0.08,0.22,0.70]); a4.scatter(sp.late_pct,sp.avg_review,s=sp.revenue/1500,alpha=.4,color="#264653"); a4.set_title("Sellers 50+ orders (bubble = revenue)",loc="left",fontsize=11); a4.set_xlabel("Late %"); a4.set_ylabel("Avg review"); a4.grid(alpha=.3)
f.savefig("dashboard/preview_page3_logistics_experience.png",dpi=110); plt.close(f)
print("done")
