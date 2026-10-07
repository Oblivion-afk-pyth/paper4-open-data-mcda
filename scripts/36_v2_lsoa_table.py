"""v2: LSOA table for all Yorkshire & Humber LSOAs (Leeds + 14 other LAs): proxy energy, stock mix, EPC fractions,
costs (2024 prices), raw-EPC baseline, metered 2024, census, IoD, fuel poverty. Built identically for every LSOA."""
import pandas as pd, numpy as np, glob, sys, zipfile, openpyxl
sys.path.insert(0,"scripts"); from harmonise import predict
GAP={"A/B":0.0,"C":0.08,"D":0.20,"E":0.34,"F/G":0.48}   # Few et al. 2023 (C, F/G); D, E interpolated
cost=pd.read_parquet("02_processed/v2/cert_costs_2024prices.parquet")["cost_2024"]
L=predict(pd.read_parquet("02_processed/v2/leeds_epc_harmonised_v2.parquet")); L["la"]="E08000035"
L.to_parquet("02_processed/v2/leeds_dwelling_predictions_v2.parquet",index=False)
sums=[]; arch=[]
def agg(h):
    h=h.copy(); g=(h.MAIN_HEAT_FUEL==1)
    h["save"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1); h["abate"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
    h["att"]=1/(1+h.EPC.map(GAP)); h["save_att"]=h.save*h.att; h["abate_att"]=h.abate*h.att
    h["cost"]=h.certificate_number.map(cost)
    h["epc_deliv"]=h.epc_primary_kwh_m2*h.tfa_m2/np.where(g,1.22,3.07)       # SAP 2012 PEFs (all certificates <= 2024)
    h["tot"]=h.pred_gas+h.pred_elec; h["gas_pg"]=h.pred_gas.where(g); h["is_gas"]=g.astype(float)
    for c,cond in [("flat",h.PROP_TYPE=="Flat"),("pre1930",h.PROP_AGE_BAND==1),("FG",h.EPC=="F/G"),("AB",h.EPC=="A/B")]: h["is_"+c]=cond.astype(float)
    cols=["tot","gas_pg","pred_elec","tfa_m2","is_gas","save","abate","save_att","abate_att","cost","epc_deliv","epc_primary_kwh_m2","is_flat","is_pre1930","is_FG","is_AB"]
    s=h.groupby("lsoa21cd")[cols].sum(min_count=1); c=h.groupby("lsoa21cd")[cols].count().add_prefix("n_")
    s["n_epc"]=h.groupby("lsoa21cd").size(); s["la"]=h.groupby("lsoa21cd").la.agg(lambda x:x.mode().iloc[0])
    sums.append(s.join(c))
    a=h.assign(arch=h.PROP_TYPE.astype(str)+"|"+h.PROP_AGE_BAND.astype(str)).groupby(["lsoa21cd","arch"]).size(); arch.append(a)
agg(L)
for p in sorted(glob.glob("02_processed/v2/yorks_dw/part*.parquet")): agg(pd.read_parquet(p))
S=pd.concat(sums); la=S.groupby(level=0).la.first(); S=S.drop(columns="la").groupby(level=0).sum()
A=pd.DataFrame(index=S.index); A["la"]=la; A["n_epc"]=S.n_epc
for c in ["tot","gas_pg","pred_elec","tfa_m2","is_gas","save","abate","save_att","abate_att","cost","epc_deliv","epc_primary_kwh_m2","is_flat","is_pre1930","is_FG","is_AB"]: A[c]=S[c]/S["n_"+c]
A=A.rename(columns={"tot":"proxy_total_mean","gas_pg":"proxy_gas_mean","pred_elec":"proxy_elec_mean","tfa_m2":"mean_tfa","is_gas":"gas_share_epc","cost":"pkg_cost_2024","epc_deliv":"epc_total_mean","epc_primary_kwh_m2":"mean_epc_primary"})
for c in ["is_flat","is_pre1930","is_FG","is_AB"]: A["pct_"+c[3:]]=A.pop(c)*100
ar=pd.concat(arch).groupby(level=[0,1]).sum(); A["C6_stock_homogeneity"]=ar.groupby(level=0).apply(lambda s:s.max()/s.sum()*100)
ids=set(A.index)
for fuel,f in [("gas","LSOA_domestic_gas_2010-2024.xlsx"),("elec","LSOA_domestic_elec_2010-2024.xlsx")]:
    ws=openpyxl.load_workbook("01_raw/metered_benchmark/"+f,read_only=True)["2024"]
    m=pd.DataFrame([(r[4],r[6],r[8]) for r in ws.iter_rows(min_row=6,values_only=True) if r and r[4] in ids],columns=["lsoa21cd",f"{fuel}_meters",f"met_{fuel}_mean"]).set_index("lsoa21cd")
    A=A.join(m)
A["met_gas_share"]=(A.gas_meters/A.elec_meters).clip(upper=1).fillna(0); A["met_total_mean"]=A.met_gas_mean.fillna(0)*A.met_gas_share+A.met_elec_mean
def cz(t):
    z=zipfile.ZipFile(f"01_raw/census/census2021-{t}.zip"); n=[x for x in z.namelist() if x.endswith("-lsoa.csv")][0]
    return pd.read_csv(z.open(n)).set_index("geography code").loc[lambda d:d.index.isin(ids)]
a=cz("ts017"); c=a.columns; hh=a[c[2]]-a[c[3]]; t=cz("ts054"); tc=t.columns; o=cz("ts052"); oc=o.columns
A=A.join(pd.DataFrame({"households":hh,"hh_size":(a[c[4:12]].values*np.arange(1,9)).sum(1)/hh,"pct_1person":a[c[4]]/hh*100,
  "pct_private_rent":t[tc[11]]/t[tc[2]]*100,"pct_social_rent":t[tc[8]]/t[tc[2]]*100,"pct_overcrowded":(o[oc[6]]+o[oc[7]])/o[oc[2]]*100,"pct_underoccupied":o[oc[3]]/o[oc[2]]*100}))
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv").set_index("LSOA code (2021)")
A["imd_score"]=iod["Index of Multiple Deprivation (IMD) Score"]; A["income_score"]=iod["Income Score (rate)"]
ws=openpyxl.load_workbook("01_raw/fuel_poverty/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx",read_only=True)["Table 4"]
A["fuel_poverty_pct"]=pd.Series({r[0]:r[7] for r in ws.iter_rows(min_row=4,values_only=True) if r and r[0] in ids})
A["epc_coverage"]=A.n_epc/A.households
lk=pd.concat([pd.read_csv("02_processed/v2/yorks_postcode_lookup_v2.csv",dtype=str),pd.read_csv("02_processed/leeds_postcode_lookup.csv",dtype=str)[["pcds","lsoa21cd","msoa21cd"]]]).drop_duplicates("lsoa21cd").set_index("lsoa21cd").msoa21cd
A["msoa21cd"]=lk
A.to_csv("02_processed/v2/lsoa_table_v2.csv")
print(A.shape, A.groupby(A.la=="E08000035").size().to_dict()); print(A.groupby("la").size().to_string()); print(A.isna().sum()[A.isna().sum()>0].to_string())
