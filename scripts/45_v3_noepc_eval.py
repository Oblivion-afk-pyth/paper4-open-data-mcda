"""v3: area correction + prediction and decision validation for the no-EPC-rating transfer models (Leeds, Bradford)."""
import pandas as pd, numpy as np, lightgbm as lgb, json, sys
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
sys.path.insert(0,"scripts"); from mcda import gra, combined_w; from mcda_v2 import *
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); N=pd.read_csv("02_processed/v3_noepc_lsoa.csv",index_col=0)
for k in ["gas","elec","total"]: A[f"proxy_{k}_mean"]=N[f"noepc_{k}_mean"]; A=A.drop(columns=[f"proxyc_{k}_mean"])
F=["hh_size","pct_1person","pct_private_rent","pct_social_rent","pct_overcrowded","pct_underoccupied","imd_score","income_score","mean_tfa","gas_share_epc","pct_flat","pct_pre1930","pct_FG","pct_AB","mean_epc_primary","epc_coverage"]
mk=lambda: lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=30,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,verbose=-1,n_jobs=2,random_state=1)
cal=A[A.la!="E08000035"]; out={}
for k in ["total","gas","elec"]:
    y=np.log(A[f"met_{k}_mean"]/A[f"proxy_{k}_mean"]); c=cal.index[y.loc[cal.index].notna()&cal[F].notna().all(1)]
    p=cross_val_predict(mk(),cal.loc[c,F],y[c],cv=LeaveOneGroupOut(),groups=cal.loc[c,"la"]); out[f"R2_LOLAO_{k}"]=round(float(1-((y[c]-p)**2).sum()/((y[c]-y[c].mean())**2).sum()),3)
    m=mk().fit(cal.loc[c,F],y[c]); L=A.la=="E08000035"; A.loc[L,f"proxyc_{k}_mean"]=A.loc[L,f"proxy_{k}_mean"]*np.exp(m.predict(A.loc[L,F]))
    cb=[i for i in c if A.loc[i,"la"]!="E08000032"]; mb=mk().fit(A.loc[cb,F],y[cb]); B=A.la=="E08000032"; A.loc[B,f"proxyc_{k}_mean"]=A.loc[B,f"proxy_{k}_mean"]*np.exp(mb.predict(A.loc[B,F]))
def l1(p,o): return dict(MAPE=round(float(100*(abs(p-o)/o).mean()),1),R2=round(float(1-((o-p)**2).sum()/((o-o.mean())**2).sum()),3),bias=round(float(100*(p.sum()-o.sum())/o.sum()),1),rho=round(float(p.corr(o,method="spearman")),3))
rows=[]
for city,la in [("leeds","E08000035"),("bradford","E08000032")]:
    C=A[A.la==la]; M=pd.read_csv(f"03_outputs/v2/matrix_{city}_T0.csv",index_col=0)
    for v,col in [("T1_noEPC","proxy"),("T1c_noEPC","proxyc")]:
        out[f"{city}_{v}_total"]=l1(C[f"{col}_total_mean"],C.met_total_mean); out[f"{city}_{v}_intensity_rho"]=round(float((C[f"{col}_total_mean"]/C.mean_tfa).corr(C.met_total_mean/C.mean_tfa,method="spearman")),3)
        P=matrix(C,"T1" if v.startswith("T1_") else "T1c").loc[M.index]
        for w in ["objective","equal","e70","e90"]:
            wP=combined_w(P) if w=="objective" else (pd.Series(1/6,index=P.columns) if w=="equal" else energy_w(P.columns,{"e70":0.7,"e90":0.9}[w]))
            rows.append(dict(city=city,proxy=v,weights=w,**agree(gra(P,wP),gra(M,wP))))
R=pd.DataFrame(rows); R.to_csv("03_outputs/v2/noepc_decision.csv",index=False); json.dump(out,open("03_outputs/v2/noepc_prediction.json","w"),indent=1)
print(json.dumps(out)); print(R.to_string(index=False))
