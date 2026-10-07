"""v2: Leeds and Bradford matrices (T0 meter-informed reference, T1, T1c) + prediction validation (Level 1)."""
import pandas as pd, numpy as np, json, sys
sys.path.insert(0,"scripts"); from mcda_v2 import *
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); out={}
def l1(p,o):
    k=p.notna()&o.notna()&(o>0); p,o=p[k],o[k]
    return dict(n=int(k.sum()),MAPE=round(float(100*(abs(p-o)/o).mean()),1),R2=round(float(1-((o-p)**2).sum()/((o-o.mean())**2).sum()),3),bias=round(float(100*(p.sum()-o.sum())/o.sum()),1),rho=round(float(p.corr(o,method="spearman")),3))
for city,la in [("leeds","E08000035"),("bradford","E08000032")]:
    C=A[A.la==la]; r={}
    r["total_rawEPC"]=l1(C.epc_total_mean,C.met_total_mean)
    for v,col in [("T1","proxy"),("T1c","proxyc")]:
        r[f"total_{v}"]=l1(C[f"{col}_total_mean"],C.met_total_mean); r[f"gas_{v}"]=l1(C[f"{col}_gas_mean"],C.met_gas_mean); r[f"elec_{v}"]=l1(C[f"{col}_elec_mean"],C.met_elec_mean)
        r[f"intensity_{v}"]=l1(C[f"{col}_total_mean"]/C.mean_tfa,C.met_total_mean/C.mean_tfa)
    for nm,src in [("T0","M"),("T1","T1"),("T1c","T1c")]:
        for suf,kw in [("",{}),("_att",{"att":True}),("_c1total",{"c1_total":True})]:
            matrix(C,src,**kw).to_csv(f"03_outputs/v2/matrix_{city}_{nm}{suf}.csv")
    X=matrix(C,"M"); r["n_complete_rows"]=int(X.dropna().shape[0]); r["n_lsoa"]=len(C); r["n_dwellings_epc"]=int(C.n_epc.sum())
    out[city]=r
json.dump(out,open("03_outputs/v2/level1_v2.json","w"),indent=1); print(json.dumps(out,indent=0)[:3000])
