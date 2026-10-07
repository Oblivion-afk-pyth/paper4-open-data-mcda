"""Build LSOA x 6 criteria matrices: proxy (ML estimates) and metered (held-out benchmark). All criteria = retrofit need (benefit type)."""
import pandas as pd, numpy as np, glob, re
EF_GAS, EF_ELEC = 0.18290, 0.20705   # kgCO2e/kWh, DESNZ GHG conversion factors 2024 (check before publication)
h=pd.read_parquet("02_processed/leeds_dwelling_predictions.parquet")
L=pd.read_csv("03_outputs/level1_lsoa_estimates_vs_metered.csv",index_col=0)
# --- EPC recommendations: indicative cost midpoint summed per certificate
def mid(s):
    v=[float(x.replace(",","")) for x in re.findall(r"£\s*([\d,]+)",str(s))]
    return np.mean(v) if v else np.nan
cost=[]
for p in glob.glob("02_processed/epc_parts/recommendations-*_leeds.csv"):
    r=pd.read_csv(p,usecols=["certificate_number","indicative_cost"],dtype=str)
    r["c"]=r.indicative_cost.map(mid); cost.append(r.groupby("certificate_number").c.sum())
cost=pd.concat(cost).groupby(level=0).sum()
h["pkg_cost_gbp"]=h.certificate_number.map(cost)
h["save_frac"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1)
h["co2_abate_frac"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
h["archetype"]=h.PROP_TYPE.astype(str)+"|"+h.PROP_AGE_BAND.astype(str)
G=h.groupby("lsoa21cd")
base=pd.DataFrame({"save_frac":G.save_frac.mean(),"co2_abate_frac":G.co2_abate_frac.mean(),"pkg_cost":G.pkg_cost_gbp.mean(),
   "C6_delivery_eff":G.archetype.agg(lambda s:s.value_counts(normalize=True).iloc[0]*100)})
fp=pd.read_csv("02_processed/leeds_lsoa_fuel_poverty_2024.csv").set_index("lsoa21cd").fp_pct
iod=pd.read_csv("02_processed/leeds_lsoa_iod2025.csv").set_index("LSOA code (2021)")["Income Score (rate)"]
def matrix(total,gas,elec,gshare):
    M=pd.DataFrame(index=L.index)
    M["C1_energy_intensity"]=total/L.mean_tfa
    carbon=(gas*gshare*EF_GAS+elec*EF_ELEC)/1000                       # tCO2e per dwelling
    M["C2_carbon_abatement"]=base.co2_abate_frac*carbon
    M["C3_fuel_poverty"]=fp
    M["C4_income_deprivation"]=iod
    M["C5_cost_effectiveness"]=base.save_frac*total/base.pkg_cost        # kWh/yr saved per £
    M["C6_delivery_eff"]=base.C6_delivery_eff
    return M
P=matrix(L.proxy_total_mean,L.proxy_gas_mean.fillna(0),L.proxy_elec_mean,L.gas_share_epc)
Mt=matrix(L.met_total_mean,L.met_gas_mean.fillna(0),L.met_elec_mean,L.met_gas_share.fillna(0))
P.to_csv("03_outputs/matrix_proxy_T1.csv"); Mt.to_csv("03_outputs/matrix_metered_T0.csv")
print("missing:",P.isna().sum().to_dict()); print(P.describe().round(2).to_string()); print(Mt[["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]].describe().round(2).to_string())
