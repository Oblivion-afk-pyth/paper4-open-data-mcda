"""Shared EPC -> NEED feature mapping and NEED-model prediction."""
import pandas as pd, numpy as np, re, lightgbm as lgb
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"],"EPC":["A/B","C","D","E","F/G"]}
FG=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","IMD_BAND_ENG","PV_FLAG"]; FE=FG+["MAIN_HEAT_FUEL"]
def _ptype(p,b):
    if p in("Flat","Maisonette"): return "Flat"
    if p=="Bungalow": return "Bungalow"
    if p=="House":
        if b=="Detached": return "Detached"
        if b=="Semi-Detached": return "Semi detached"
        if "Mid-Terrace" in str(b): return "Mid terrace"
        if "End-Terrace" in str(b): return "End terrace"
    return np.nan
def _age(s):
    s=str(s)
    if "before 1900" in s: return 1
    y=re.findall(r"(1[89]\d\d|20\d\d)",s)
    if not y: return np.nan
    y=int(y[0]); return 1 if y<1930 else 2 if y<1973 else 3 if y<2000 else 4
def _fuel(f,flag):
    f=str(f).lower()
    if f=="nan": return 1 if flag=="Y" else 2
    return 1 if ("mains gas" in f and "(community)" not in f) else 2
def harmonise(e,imd_decile):
    tfa=pd.to_numeric(e.total_floor_area,errors="coerce").where(lambda x:(x>=15)&(x<=1000))
    h=pd.DataFrame({"lsoa21cd":e.lsoa21cd.values,"certificate_number":e.certificate_number.values,"tfa_m2":tfa.values,
      "PROP_TYPE":[_ptype(p,b) for p,b in zip(e.property_type,e.built_form)],
      "PROP_AGE_BAND":e.construction_age_band.map(_age).values,
      "FLOOR_AREA_BAND":pd.cut(tfa,[0,50,100,150,200,1e9],labels=[1,2,3,4,5]).astype(float).values,
      "EPC":e.current_energy_rating.map({"A":"A/B","B":"A/B","C":"C","D":"D","E":"E","F":"F/G","G":"F/G"}).values,
      "MAIN_HEAT_FUEL":[_fuel(f,g) for f,g in zip(e.main_fuel,e.mains_gas_flag)],
      "PV_FLAG":(pd.to_numeric(e.photo_supply,errors="coerce").fillna(0)>0).astype(int).values,
      "IMD_BAND_ENG":np.ceil(e.lsoa21cd.map(imd_decile)/2).values,
      "epc_primary_kwh_m2":pd.to_numeric(e.energy_consumption_current,errors="coerce").values,
      "epc_potential_kwh_m2":pd.to_numeric(e.energy_consumption_potential,errors="coerce").values,
      "co2_current_t":pd.to_numeric(e.co2_emissions_current,errors="coerce").values,
      "co2_potential_t":pd.to_numeric(e.co2_emissions_potential,errors="coerce").values})
    return h
def _prep(x,feat):
    x=x[feat].copy()
    for c,v in CATS.items(): x[c]=pd.Categorical(x[c].astype(str),categories=v)
    for c in feat:
        if c not in CATS: x[c]=x[c].astype(float)
    return x
def predict(h):
    h=h.copy()
    h["pred_gas"]=lgb.Booster(model_file="models/need_transfer_gas.txt").predict(_prep(h,FG))*(h.MAIN_HEAT_FUEL==1)
    h["pred_elec"]=lgb.Booster(model_file="models/need_transfer_elec.txt").predict(_prep(h,FE))
    return h
def lsoa_aggregate(h):
    G=h.groupby("lsoa21cd"); gh=h[h.MAIN_HEAT_FUEL==1]
    return pd.DataFrame({"n_epc":G.size(),"proxy_gas_mean":gh.groupby("lsoa21cd").pred_gas.mean(),"proxy_elec_mean":G.pred_elec.mean(),
      "proxy_total_mean":(h.pred_gas+h.pred_elec).groupby(h.lsoa21cd).mean(),"mean_tfa":G.tfa_m2.mean(),
      "gas_share_epc":(h.MAIN_HEAT_FUEL==1).groupby(h.lsoa21cd).mean(),
      "pct_flat":(h.PROP_TYPE=="Flat").groupby(h.lsoa21cd).mean()*100,"pct_pre1930":(h.PROP_AGE_BAND==1).groupby(h.lsoa21cd).mean()*100,
      "pct_FG":(h.EPC=="F/G").groupby(h.lsoa21cd).mean()*100,"pct_AB":(h.EPC=="A/B").groupby(h.lsoa21cd).mean()*100,
      "mean_epc_primary":G.epc_primary_kwh_m2.mean()})
