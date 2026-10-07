"""Area-level correction (T1c): learn log(metered/proxy) from open LSOA features on Yorkshire LSOAs outside Leeds; apply to Leeds.
Leeds meters are used only for evaluation."""
import pandas as pd, numpy as np, lightgbm as lgb, json, sys
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold, cross_val_predict
sys.path.insert(0,"scripts"); from mcda import *
A=pd.read_csv("02_processed/calibration_table.csv",index_col=0)
F=["hh_size","pct_1person","pct_private_rent","pct_social_rent","pct_overcrowded","pct_underoccupied","imd_score","income_score",
   "mean_tfa","gas_share_epc","pct_flat","pct_pre1930","pct_FG","pct_AB","mean_epc_primary","epc_coverage"]
cal=A[A.set=="calib"]; lee=A[A.set=="leeds"].copy()
out={}
for k in ["total","gas","elec"]:
    c=cal.dropna(subset=F+[f"y_{k}"])
    lg=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=30,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,verbose=-1,n_jobs=2,random_state=1)
    rd=make_pipeline(StandardScaler(),RidgeCV(alphas=np.logspace(-2,3,20)))
    cv={}
    for name,m in [("lgbm",lg),("ridge",rd)]:
        p=cross_val_predict(m,c[F],c[f"y_{k}"],cv=KFold(5,shuffle=True,random_state=1))
        y=c[f"y_{k}"]; cv[name]=round(1-((y-p)**2).sum()/((y-y.mean())**2).sum(),3)
    best=max(cv,key=cv.get); m={"lgbm":lg,"ridge":rd}[best].fit(c[F],c[f"y_{k}"])
    lee[f"corr_{k}"]=np.exp(m.predict(lee[F].fillna(c[F].median())))
    out[k]=dict(cv_r2=cv,chosen=best)
for k in ["total","gas","elec"]: lee[f"proxyc_{k}_mean"]=lee[f"proxy_{k}_mean"]*lee[f"corr_{k}"]
def met(p,o):
    k=p.notna()&o.notna(); p,o=p[k],o[k]
    return dict(MAPE=round(100*(abs(p-o)/o).mean(),1),R2=round(1-((o-p)**2).sum()/((o-o.mean())**2).sum(),3),bias=round(100*(p.sum()-o.sum())/o.sum(),1),rho=round(pd.Series(p).corr(pd.Series(o),method="spearman"),3))
rows=[]
for k in ["total","gas","elec"]:
    rows.append(dict(quantity=k,version="T1 proxy",**met(lee[f"proxy_{k}_mean"],lee[f"met_{k}_mean"])))
    rows.append(dict(quantity=k,version="T1c corrected",**met(lee[f"proxyc_{k}_mean"],lee[f"met_{k}_mean"])))
    rows.append(dict(quantity=k+" per m2",version="T1 proxy",**met(lee[f"proxy_{k}_mean"]/lee.mean_tfa,lee[f"met_{k}_mean"]/lee.mean_tfa)))
    rows.append(dict(quantity=k+" per m2",version="T1c corrected",**met(lee[f"proxyc_{k}_mean"]/lee.mean_tfa,lee[f"met_{k}_mean"]/lee.mean_tfa)))
R=pd.DataFrame(rows); R.to_csv("03_outputs/level1_T1c_correction.csv",index=False)
lee.to_csv("02_processed/leeds_lsoa_T1c.csv")
json.dump(out,open("models/correction_cv.json","w"),indent=1)
# rebuild proxy matrix with corrected energy (C1,C5 scale with total; C2 with carbon)
P=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0); M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0)
EG,EE=0.18290,0.20705
carb=lambda g,e,s:(g.fillna(0)*s*EG+e*EE)
Pc=P.copy(); f_tot=lee.proxyc_total_mean/lee.proxy_total_mean
Pc["C1_energy_intensity"]*=f_tot; Pc["C5_cost_effectiveness"]*=f_tot
Pc["C2_carbon_abatement"]*=carb(lee.proxyc_gas_mean,lee.proxyc_elec_mean,lee.gas_share_epc)/carb(lee.proxy_gas_mean,lee.proxy_elec_mean,lee.gas_share_epc)
Pc.to_csv("03_outputs/matrix_proxy_T1c.csv")
rows=[]
for nm,X in [("T1",P),("T1c",Pc)]:
    rows.append(dict(version=nm,case="GRA objective weights",**compare(gra(X,combined_w(X)),gra(M,combined_w(M)))))
    eq=pd.Series(1/6,index=M.columns); rows.append(dict(version=nm,case="GRA equal weights",**compare(gra(X,eq),gra(M,eq))))
    E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]
    w9=pd.Series({c:(0.3 if c in E else 0.1/3) for c in M.columns}); rows.append(dict(version=nm,case="GRA energy 90%",**compare(gra(X,w9),gra(M,w9))))
    rows.append(dict(version=nm,case="C1 alone",**compare(X.C1_energy_intensity,M.C1_energy_intensity)))
R2=pd.DataFrame(rows); R2.to_csv("03_outputs/level2_T1_vs_T1c.csv",index=False)
print(json.dumps(out)); print(R.to_string(index=False)); print(R2.to_string(index=False))
