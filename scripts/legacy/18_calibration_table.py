"""Build LSOA feature table (census, IoD, stock) + metered 2024 targets for Yorkshire calibration LSOAs and Leeds."""
import pandas as pd, numpy as np, openpyxl, zipfile
Y=pd.read_csv("02_processed/yorks_lsoa_proxy.csv",index_col=0); Y["set"]="calib"
Lh=pd.read_parquet("02_processed/leeds_dwelling_predictions.parquet")
import sys; sys.path.insert(0,"scripts"); from harmonise import lsoa_aggregate
Lh["certificate_number"]=Lh.certificate_number
L=lsoa_aggregate(Lh); L["set"]="leeds"
A=pd.concat([Y,L]); ids=set(A.index)
met={}
for fuel,f in [("gas","LSOA_domestic_gas_2010-2024.xlsx"),("elec","LSOA_domestic_elec_2010-2024.xlsx")]:
    ws=openpyxl.load_workbook("01_raw/metered_benchmark/"+f,read_only=True)["2024"]
    rows=[(r[4],r[6],r[8]) for r in ws.iter_rows(min_row=6,values_only=True) if r and r[4] in ids]
    met[fuel]=pd.DataFrame(rows,columns=["lsoa21cd",f"{fuel}_meters",f"met_{fuel}_mean"]).set_index("lsoa21cd")
A=A.join(met["gas"]).join(met["elec"])
A["met_gas_share"]=(A.gas_meters/A.elec_meters).clip(upper=1).fillna(0)
A["met_total_mean"]=A.met_gas_mean.fillna(0)*A.met_gas_share+A.met_elec_mean
def cz(t):
    z=zipfile.ZipFile(f"01_raw/census/census2021-{t}.zip"); n=[x for x in z.namelist() if x.endswith("-lsoa.csv")][0]
    c=pd.read_csv(z.open(n)); return c.set_index("geography code").loc[lambda d:d.index.isin(ids)]
a=cz("ts017"); c=a.columns; hh=a[c[2]]-a[c[3]]
t=cz("ts054"); tc=t.columns; o=cz("ts052"); oc=o.columns
C=pd.DataFrame({"households":hh,"hh_size":(a[c[4:12]].values*np.arange(1,9)).sum(1)/hh,"pct_1person":a[c[4]]/hh*100,
  "pct_private_rent":t[tc[11]]/t[tc[2]]*100,"pct_social_rent":t[tc[8]]/t[tc[2]]*100,
  "pct_overcrowded":(o[oc[6]]+o[oc[7]])/o[oc[2]]*100,"pct_underoccupied":o[oc[3]]/o[oc[2]]*100})
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv").set_index("LSOA code (2021)")
C["imd_score"]=iod["Index of Multiple Deprivation (IMD) Score"]; C["income_score"]=iod["Income Score (rate)"]
A=A.join(C); A["epc_coverage"]=A.n_epc/A.households
for k in ["total","gas","elec"]: A[f"y_{k}"]=np.log(A[f"met_{k}_mean"]/A[f"proxy_{k}_mean"])
A.to_csv("02_processed/calibration_table.csv")
print(A.groupby("set").size().to_string()); print(A.groupby("set")[["y_total","y_gas","y_elec"]].agg(["mean","std"]).round(3).to_string())
print("missing targets calib:",A[A.set=="calib"][["y_total","y_gas","y_elec"]].isna().sum().to_dict())
