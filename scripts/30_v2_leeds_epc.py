"""v2 (revision): latest Leeds EPC per dwelling lodged ON OR BEFORE 2024-12-31, harmonised to NEED."""
import pandas as pd, glob, sys, json
sys.path.insert(0,"scripts"); from harmonise import harmonise
CUT=pd.Timestamp("2024-12-31 23:59:59")
USE=["certificate_number","uprn","address","postcode","lodgement_datetime","lodgement_date","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential"]
parts=sorted(glob.glob("02_processed/epc_parts/certificates-*_leeds.csv"))
d=pd.concat((pd.read_csv(p,dtype=str,usecols=USE) for p in parts),ignore_index=True); n_all=len(d)
d["t"]=pd.to_datetime(d.lodgement_datetime.fillna(d.lodgement_date),errors="coerce")
n_after=int((d.t>CUT).sum()); n_nat=int(d.t.isna().sum()); d=d[d.t<=CUT]; n_pre=len(d)
d["key"]=d.uprn.where(d.uprn.notna()&(d.uprn!=""),"ADDR|"+d.address.str.upper().str.strip()+"|"+d.postcode.str.upper().str.strip())
d=d.sort_values("t").drop_duplicates("key",keep="last")
lk=pd.read_csv("02_processed/leeds_postcode_lookup.csv",dtype=str)[["pcds","lsoa21cd","msoa21cd"]]
d["pc"]=d.postcode.str.upper().str.strip(); d=d.merge(lk,left_on="pc",right_on="pcds",how="left")
n_dw=len(d); dl=d[d.lsoa21cd.notna()].reset_index(drop=True)
iod=pd.read_csv("02_processed/leeds_lsoa_iod2025.csv").set_index("LSOA code (2021)")["Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)"]
h=harmonise(dl,iod); h["msoa21cd"]=dl.msoa21cd.values; h["lodgement_year"]=dl.t.dt.year.values; h["uprn"]=dl.uprn.values
h.to_parquet("02_processed/v2/leeds_epc_harmonised_v2.parquet",index=False)
miss={k:int(v) for k,v in h[["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","IMD_BAND_ENG","tfa_m2","epc_primary_kwh_m2","epc_potential_kwh_m2","co2_current_t","co2_potential_t"]].isna().sum().items()}
out=dict(certificates_2008_2026=n_all,lodged_after_2024=n_after,no_date=n_nat,certificates_to_2024=n_pre,dwellings=n_dw,linked_to_lsoa=len(h),lsoas=int(h.lsoa21cd.nunique()),gas_share=round(float((h.MAIN_HEAT_FUEL==1).mean()),3),missing=miss)
json.dump(out,open("03_outputs/v2/epc_leeds_v2_counts.json","w"),indent=1); print(json.dumps(out))
