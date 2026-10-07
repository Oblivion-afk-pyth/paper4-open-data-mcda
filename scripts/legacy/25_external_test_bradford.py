"""External test: hold out Bradford (E08000032) from the area correction; run full pipeline on Bradford vs its own meters.
NEED transfer models (trained outside Yorkshire) unchanged. Costs for C5 use Leeds group means by type x floor-area band."""
import pandas as pd, numpy as np, lightgbm as lgb, sys, glob, re, json, openpyxl
sys.path.insert(0,"scripts"); from harmonise import harmonise, predict; from mcda import *
LA="E08000032"; EG,EE=0.18290,0.20705
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv").set_index("LSOA code (2021)")
dec=iod["Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)"]
USE=["certificate_number","local_authority","lsoa21cd","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential"]
e=pd.read_csv("02_processed/yorks_epc_latest.csv",dtype=str,usecols=USE)
la_of=e.groupby("lsoa21cd").local_authority.agg(lambda s:s.mode().iloc[0])
e=e[e.local_authority==LA]
h=predict(harmonise(e,dec))
h["save_frac"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1); h["abate"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
h["arch"]=h.PROP_TYPE.astype(str)+"|"+h.PROP_AGE_BAND.astype(str)
# Leeds cost lookup by type x floor-area band
lh=pd.read_parquet("02_processed/leeds_dwelling_predictions.parquet")
def mid(s):
    v=[float(x.replace(",","")) for x in re.findall(r"£\s*([\d,]+)",str(s))]; return np.mean(v) if v else np.nan
cost=pd.concat(pd.read_csv(p,usecols=["certificate_number","indicative_cost"],dtype=str).assign(c=lambda d:d.indicative_cost.map(mid)).groupby("certificate_number").c.sum() for p in glob.glob("02_processed/epc_parts/recommendations-*_leeds.csv")).groupby(level=0).sum()
lh["cost"]=lh.certificate_number.map(cost); CT=lh.groupby(["PROP_TYPE","FLOOR_AREA_BAND"]).cost.mean()
h["cost"]=[CT.get((a,b),lh.cost.mean()) for a,b in zip(h.PROP_TYPE,h.FLOOR_AREA_BAND)]
A=pd.read_csv("02_processed/calibration_table.csv",index_col=0); A["la"]=A.index.map(la_of)
B=A[(A.set=="calib")&(A.la==LA)].copy(); cal=A[(A.set=="calib")&(A.la!=LA)]
F=["hh_size","pct_1person","pct_private_rent","pct_social_rent","pct_overcrowded","pct_underoccupied","imd_score","income_score","mean_tfa","gas_share_epc","pct_flat","pct_pre1930","pct_FG","pct_AB","mean_epc_primary","epc_coverage"]
for k in ["total","gas","elec"]:
    c=cal.dropna(subset=F+[f"y_{k}"])
    m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=30,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,verbose=-1,n_jobs=2,random_state=1).fit(c[F],c[f"y_{k}"])
    B[f"proxyc_{k}_mean"]=B[f"proxy_{k}_mean"]*np.exp(m.predict(B[F].fillna(c[F].median())))
G=h.groupby("lsoa21cd")
base=pd.DataFrame({"abate":G.abate.mean(),"save":G.save_frac.mean(),"cost":G.cost.mean(),"C6":G.arch.agg(lambda s:s.value_counts(normalize=True).iloc[0]*100)}).reindex(B.index)
ws=openpyxl.load_workbook("01_raw/fuel_poverty/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx",read_only=True)["Table 4"]
fp=pd.Series({r[0]:r[7] for r in ws.iter_rows(min_row=4,values_only=True) if r[2]==LA})
def mat(tot,gas,el,share):
    X=pd.DataFrame(index=B.index)
    X["C1_energy_intensity"]=tot/B.mean_tfa
    X["C2_carbon_abatement"]=base.abate*(gas.fillna(0)*share*EG+el*EE)/1000
    X["C3_fuel_poverty"]=fp.reindex(B.index); X["C4_income_deprivation"]=iod["Income Score (rate)"].reindex(B.index)
    X["C5_cost_effectiveness"]=base.save*tot/base.cost; X["C6_delivery_eff"]=base.C6
    return X.dropna()
M=mat(B.met_total_mean,B.met_gas_mean,B.met_elec_mean,B.met_gas_share)
P1=mat(B.proxy_total_mean,B.proxy_gas_mean,B.proxy_elec_mean,B.gas_share_epc).reindex(M.index)
Pc=mat(B.proxyc_total_mean,B.proxyc_gas_mean,B.proxyc_elec_mean,B.gas_share_epc).reindex(M.index)
def l1(p,o):
    k=p.notna()&o.notna(); p,o=p[k],o[k]
    return dict(MAPE=round(100*(abs(p-o)/o).mean(),1),R2=round(1-((o-p)**2).sum()/((o-o.mean())**2).sum(),3),bias=round(100*(p.sum()-o.sum())/o.sum(),1),rho=round(p.corr(o,method="spearman"),3))
res={"n_lsoa":len(M),"n_dwellings":len(h),"n_calib_lsoa":len(cal),
 "L1_total_T1":l1(B.proxy_total_mean,B.met_total_mean),"L1_total_T1c":l1(B.proxyc_total_mean,B.met_total_mean),
 "L1_C1_T1":l1(P1.C1_energy_intensity,M.C1_energy_intensity),"L1_C1_T1c":l1(Pc.C1_energy_intensity,M.C1_energy_intensity)}
eq=pd.Series(1/6,index=M.columns)
for nm,X in [("T1",P1),("T1c",Pc)]:
    res[f"L2_{nm}_objective"]=compare(gra(X,combined_w(X)),gra(M,combined_w(M)))
    res[f"L2_{nm}_equal"]=compare(gra(X,eq),gra(M,eq))
    res[f"L2_{nm}_TOPSIS_objective"]=compare(topsis(X,combined_w(X)),topsis(M,combined_w(M)))
res["weights_metered"]=combined_w(M).round(3).to_dict()
json.dump(res,open("03_outputs/external_test_bradford.json","w"),indent=1); print(json.dumps(res,indent=1))
