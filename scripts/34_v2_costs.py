"""v2: package cost per certificate, 2024 prices.
Rules: indicative_cost parsed to range midpoint (single values taken as given); one value per (certificate, improvement_id) –
duplicate measure codes counted once; unparseable/blank costs excluded and counted; cost deflated from the certificate's
lodgement year (= recommendations file year) to 2024 with CPIH (ONS series L522, 2015=100)."""
import pandas as pd, numpy as np, glob, re, json
CPIH={2008:86.2,2009:87.9,2010:90.1,2011:93.6,2012:96.0,2013:98.2,2014:99.6,2015:100.0,2016:101.0,2017:103.6,2018:106.0,2019:107.8,2020:108.9,2021:111.6,2022:120.5,2023:128.6,2024:132.9}
def mid(s):
    v=[float(x.replace(",","")) for x in re.findall(r"£\s*([\d,]+)",str(s))]; return np.mean(v) if v else np.nan
out=[]; st=dict(rows=0,dup_measures=0,unpriced=0)
for p in sorted(glob.glob("02_processed/v2/recs_parts/recommendations-*_v2.csv")):
    yr=int(re.search(r"recommendations-(\d{4})",p).group(1))
    if yr>2024: continue
    r=pd.read_csv(p,dtype=str); st["rows"]+=len(r)
    n0=len(r); r=r.drop_duplicates(["certificate_number","improvement_id"]); st["dup_measures"]+=n0-len(r)
    r["c"]=r.indicative_cost.map(mid); st["unpriced"]+=int(r.c.isna().sum())
    g=r.groupby("certificate_number").agg(cost_nominal=("c","sum"),n_measures=("c","size"),n_priced=("c","count"))
    g.loc[g.n_priced==0,"cost_nominal"]=np.nan
    g["cost_2024"]=g.cost_nominal*CPIH[2024]/CPIH[yr]; g["price_year"]=yr; out.append(g)
C=pd.concat(out); C.to_parquet("02_processed/v2/cert_costs_2024prices.parquet")
st.update(certificates_with_recs=len(C),certs_all_unpriced=int(C.cost_2024.isna().sum()),median_cost_2024=round(float(C.cost_2024.median())))
json.dump(st,open("03_outputs/v2/cost_processing_stats.json","w"),indent=1); print(st)
