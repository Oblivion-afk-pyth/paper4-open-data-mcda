"""Predict Leeds dwelling gas/electricity with NEED transfer models, aggregate to LSOA, compare with held-out metered data (Level 1).
Baseline: raw EPC calculated energy (primary kWh/m2 x floor area / primary energy factor; SAP 2012 factors gas 1.22, electricity 3.07; RdSAP10 (lodged >= 2025-06) gas 1.130, electricity 1.501)."""
import numpy as np, pandas as pd, lightgbm as lgb, json
from scipy.stats import spearmanr
h=pd.read_parquet("02_processed/leeds_epc_harmonised.parquet")
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"],"EPC":["A/B","C","D","E","F/G"]}
def prep(x,feat):
    x=x[feat].copy()
    for c,v in CATS.items(): x[c]=pd.Categorical(x[c].astype(str),categories=v)
    for c in feat:
        if c not in CATS: x[c]=x[c].astype(float)
    return x
FG=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","IMD_BAND_ENG","PV_FLAG"]; FE=FG+["MAIN_HEAT_FUEL"]
h["pred_gas"]=lgb.Booster(model_file="models/need_transfer_gas.txt").predict(prep(h,FG))*(h.MAIN_HEAT_FUEL==1)
h["pred_elec"]=lgb.Booster(model_file="models/need_transfer_elec.txt").predict(prep(h,FE))
new=(h.lodgement_year>=2026)|((h.lodgement_year==2025))  # approx RdSAP10 period
pef=np.where(h.MAIN_HEAT_FUEL==1,np.where(new,1.130,1.22),np.where(new,1.501,3.07))
h["epc_delivered_kwh"]=h.epc_primary_kwh_m2*h.tfa_m2/pef
h.to_parquet("02_processed/leeds_dwelling_predictions.parquet",index=False)
gas_h=h[h.MAIN_HEAT_FUEL==1]
L=pd.DataFrame({"n_epc":h.groupby("lsoa21cd").size(),
  "proxy_gas_mean":gas_h.groupby("lsoa21cd").pred_gas.mean(),
  "proxy_elec_mean":h.groupby("lsoa21cd").pred_elec.mean(),
  "proxy_total_mean":(h.pred_gas+h.pred_elec).groupby(h.lsoa21cd).mean(),
  "epc_total_mean":h.groupby("lsoa21cd").epc_delivered_kwh.mean(),
  "epc_gas_mean":gas_h.groupby("lsoa21cd").epc_delivered_kwh.mean(),
  "mean_tfa":h.groupby("lsoa21cd").tfa_m2.mean(),
  "gas_share_epc":(h.MAIN_HEAT_FUEL==1).groupby(h.lsoa21cd).mean()})
g=pd.read_csv("02_processed/leeds_lsoa_gas_2019_2024.csv").query("year==2024").set_index("lsoa21cd")
e=pd.read_csv("02_processed/leeds_lsoa_elec_2019_2024.csv").query("year==2024").set_index("lsoa21cd")
L["met_gas_mean"]=g.mean_kwh; L["met_elec_mean"]=e.mean_kwh
L["met_gas_share"]=(g.n_meters/e.n_meters).clip(upper=1)
L["met_total_mean"]=L.met_gas_mean.fillna(0)*L.met_gas_share.fillna(0)+L.met_elec_mean
L.to_csv("03_outputs/level1_lsoa_estimates_vs_metered.csv")
def m(p,o,name):
    k=p.notna()&o.notna()&(o>0); p,o=p[k],o[k]
    return dict(quantity=name,n_lsoa=int(k.sum()),MAPE_pct=round(100*(np.abs(p-o)/o).mean(),1),
      R2=round(1-((o-p)**2).sum()/((o-o.mean())**2).sum(),3),bias_pct=round(100*(p.sum()-o.sum())/o.sum(),1),
      pearson_r=round(np.corrcoef(p,o)[0,1],3),spearman_rho=round(spearmanr(p,o).correlation,3))
R=[m(L.proxy_gas_mean,L.met_gas_mean,"gas per gas-heated dwelling – ML proxy"),
   m(L.epc_gas_mean,L.met_gas_mean,"gas per gas-heated dwelling – raw EPC"),
   m(L.proxy_elec_mean,L.met_elec_mean,"electricity per dwelling – ML proxy"),
   m(L.proxy_total_mean,L.met_total_mean,"total energy per dwelling – ML proxy"),
   m(L.epc_total_mean,L.met_total_mean,"total energy per dwelling – raw EPC")]
R=pd.DataFrame(R); R.to_csv("03_outputs/level1_metrics.csv",index=False); print(R.to_string(index=False))
