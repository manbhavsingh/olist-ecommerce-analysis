import pgserver, psycopg2, sys
sys.path.insert(0,"src")
from load_postgres import load
srv=pgserver.get_server("./pgdata", cleanup_mode=None)
uri=srv.get_uri(); print(uri)
conn=psycopg2.connect(uri)
load(conn,"sql/01_schema.sql","sql/02_clean_view.sql")
cur=conn.cursor()
for t in ["customers","sellers","products","orders","order_items","reviews","payments"]:
    cur.execute(f"select count(*) from {t}"); print(t,cur.fetchone()[0])
for v in ["v_sales","v_orders"]:
    cur.execute(f"select count(*), round(sum({'price' if v=='v_sales' else 'revenue'}),2) from {v}"); print(v,cur.fetchone())
