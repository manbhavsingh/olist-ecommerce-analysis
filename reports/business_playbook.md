# Olist E-Commerce Performance Action Playbook
Data: 96,470 delivered orders, Sep 2016 - Aug 2018, revenue R$13.22M (item price, excl. freight).

## Finding 1: Late deliveries are concentrated and are associated with lower reviews
**Evidence:** 8.11% of orders are late (95% CI 7.94-8.29%). MA 19.7%, CE 15.3%, BA 14.0%, RJ 13.5% vs SP 5.9%. These 4 states produce 31.4% of all late orders. Late orders average 2.57 stars vs 4.29 on-time; 1-star share is 46.2% vs 6.6% (Mann-Whitney U, p < 0.001, rank-biserial r = -0.55). Reviews by delay: 3.77 (1-3 days late), 2.32 (3-7 days), 1.73 (7+ days). Median delivery is 10.2 days vs a median promise of 23 days, so lateness is a tail problem (4.72% of orders take 30+ days).
**Business implication:** A fixable minority of lanes and sellers drives the review damage.
**Recommended action:** Target RJ, BA, MA and CE first. RJ has about 936 more late orders than it would at SP's late rate. Set promise dates by state from p90 delivery time (e.g. PA 39.2 days, MA 34.3 days).

## Finding 2: Growth is new-customer volume; almost nobody comes back
**Evidence:** Jan-Aug 2018 vs 2017: revenue +141.1%, orders +139.9%, AOV +0.5% (R$136.08 to R$136.75). 3.0% of 93,350 customers ordered more than once; month-1 cohort retention averages 0.47%; returning customers are about 2% of orders (Jan 2017-Aug 2018). Monthly revenue plateaued at R$0.95-0.98M in Mar-May 2018 and was R$0.84M in Aug (-14.2% vs May). Top 10% of customers give 41.1% of revenue.
**Business implication:** Revenue depends on continuously buying new customers, and growth has stalled at that ceiling. Customers whose first delivered order was late show a lower repeat rate (3.18% vs 4.04%, chi-square p = 0.005; Cramer's V ≈ 0.012), but the association is small, so delivery changes alone should not be assumed to fix retention.
**Recommended action:** Launch a retention program (second-order incentive, re-engagement of top-decile customers) and track month-1 and month-3 cohort retention as headline KPIs.

## Finding 3: Revenue is concentrated in a few markets, categories and sellers
**Evidence:** SP 38.3% of revenue, SP+RJ+MG 63.4%. Top 5 categories 39.8% (health_beauty 9.3%, watches_gifts 8.8%, bed_bath_table 7.7%). Top 10% of sellers earn 67.1% of item revenue. Among 425 sellers with 50+ orders, order-weighted late % and average review correlate at -0.50; 35 sellers are more than 15% late. (Seller metrics use one seller-order row per order to avoid multi-item order weighting.)
**Business implication:** RJ is the #2 market (13.3% of revenue) with a 13.5% late rate, so it is the highest-value place to fix delivery.
**Recommended action:** Put the 31 high-late sellers on a performance review with a lateness threshold, and test basket-building offers in the top categories (AOV is flat at about R$136; this is a hypothesis to test, not an analysis result).

## Priority Actions
- **30 days:** Weekly late-% monitor by state and seller (dashboard page 3). Flag the 35 sellers above 15% late.
- **60 days:** Recalibrate promise dates by state. Start seller reviews. Design a second-order retention pilot for one cohort.
- **90 days:** Run the pilot against the 3.0% repeat baseline. Re-measure late % in RJ against SP's 5.9% and the average review of late orders.

**Limits:** Associations, not proven causes. Tests do not control for state, category or seller. Data is 2016-2018 from one marketplace.
