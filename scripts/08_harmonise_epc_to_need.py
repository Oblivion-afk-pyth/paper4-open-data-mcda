"""Map Leeds EPC dwellings onto NEED 2026 feature categories."""
import pandas as pd, numpy as np, re
USE=["uprn","certificate_number","lsoa21cd","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential","lodgement_datetime"]
e=pd.read_csv("02_processed/epc_leeds_latest.csv",dtype=str,usecols=USE)
def ptype(r):
    p,b=str(r.property_type),str(r.built_form)
    if p in("Flat","Maisonette"): return "Flat"
    if p=="Bungalow": return "Bungalow"
    if p=="House":
        if b=="Detached": return "Detached"
        if b=="Semi-Detached": return "Semi detached"
        if "Mid-Terrace" in b: return "Mid terrace"
        if "End-Terrace" in b: return "End terrace"
    return np.nan
def ageband(s):
    s=str(s)
    if "before 1900" in s: return 1
    yrs=[int(x) for x in re.findall(r"(1[89]\d\d|20\d\d)",s)]
    if not yrs: return np.nan
    y=yrs[0]
    return 1 if y<1930 else 2 if y<1973 else 3 if y<2000 else 4
def fuel(r):
    f=str(r.main_fuel).lower()
    if f=="nan": return 1 if r.mains_gas_flag=="Y" else 2
    return 1 if ("mains gas" in f and "(community)" not in f) else 2   # individual mains-gas meter
tfa=pd.to_numeric(e.total_floor_area,errors="coerce").where(lambda x:(x>=15)&(x<=1000))
iod=pd.read_csv("02_processed/leeds_lsoa_iod2025.csv")
dec=iod.set_index("LSOA code (2021)")["Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)"]
h=pd.DataFrame({
 "uprn":e.uprn,"certificate_number":e.certificate_number,"lsoa21cd":e.lsoa21cd,"tfa_m2":tfa,
 "PROP_TYPE":e.apply(ptype,axis=1),
 "PROP_AGE_BAND":e.construction_age_band.map(ageband),
 "FLOOR_AREA_BAND":pd.cut(tfa,[0,50,100,150,200,1e9],labels=[1,2,3,4,5]).astype(float),
 "EPC":e.current_energy_rating.map({"A":"A/B","B":"A/B","C":"C","D":"D","E":"E","F":"F/G","G":"F/G"}),
 "MAIN_HEAT_FUEL":e.apply(fuel,axis=1),
 "PV_FLAG":(pd.to_numeric(e.photo_supply,errors="coerce").fillna(0)>0).astype(int),
 "IMD_BAND_ENG":np.ceil(e.lsoa21cd.map(dec)/2),
 "epc_primary_kwh_m2":pd.to_numeric(e.energy_consumption_current,errors="coerce"),
 "epc_potential_kwh_m2":pd.to_numeric(e.energy_consumption_potential,errors="coerce"),
 "co2_current_t":pd.to_numeric(e.co2_emissions_current,errors="coerce"),
 "co2_potential_t":pd.to_numeric(e.co2_emissions_potential,errors="coerce"),
 "lodgement_year":pd.to_datetime(e.lodgement_datetime,errors="coerce").dt.year,
 "built_form_raw":e.built_form,"age_raw":e.construction_age_band})
h=h[h.lsoa21cd.notna()]
h.to_parquet("02_processed/leeds_epc_harmonised.parquet",index=False)
print(len(h)); print(h[["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","MAIN_HEAT_FUEL","IMD_BAND_ENG"]].isna().mean().round(3).to_string())
for c in ["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","MAIN_HEAT_FUEL","IMD_BAND_ENG"]: print(c, h[c].value_counts(normalize=True).round(3).to_dict())
