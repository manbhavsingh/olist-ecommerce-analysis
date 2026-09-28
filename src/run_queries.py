import pgserver, pandas as pd, re, sys
pd.set_option("display.width",200); pd.set_option("display.max_columns",20); pd.set_option("display.max_rows",60)
srv=pgserver.get_server("./pgdata", cleanup_mode=None)
import psycopg2; conn=psycopg2.connect(srv.get_uri())
txt=open("sql/03_analysis_queries.sql").read()
parts=re.split(r"(?m)^-- (Q\d+ .*)$",txt)
only=sys.argv[1:]
for i in range(1,len(parts),2):
    name,q=parts[i],parts[i+1]
    if only and name.split()[0] not in only: continue
    print("\n###",name); print(pd.read_sql(q.strip().rstrip(";"),conn).to_string(index=False))
