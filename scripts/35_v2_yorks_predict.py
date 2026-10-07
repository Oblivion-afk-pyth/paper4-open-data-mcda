"""v2: harmonise + predict Yorkshire (excl. Leeds) dwellings in chunks; resumable."""
import pandas as pd, sys, os
sys.path.insert(0,"scripts"); from harmonise import harmonise, predict
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",usecols=[0,6]); dec=iod.set_index(iod.columns[0])[iod.columns[1]]
lk=pd.read_csv("02_processed/v2/yorks_postcode_lookup_v2.csv",dtype=str).set_index("pcds")
USE=["certificate_number","local_authority","postcode","t","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential"]
for i,ch in enumerate(pd.read_csv("02_processed/v2/yorks_epc_latest_v2.csv",usecols=USE,dtype=str,chunksize=250_000)):
    out=f"02_processed/v2/yorks_dw/part{i:02d}.parquet"
    if os.path.exists(out): continue
    pc=ch.postcode.str.upper().str.strip(); ch=ch.assign(lsoa21cd=pc.map(lk.lsoa21cd).values,msoa21cd=pc.map(lk.msoa21cd).values)
    ch=ch[ch.lsoa21cd.notna()].reset_index(drop=True)
    h=predict(harmonise(ch,dec)); h["msoa21cd"]=ch.msoa21cd.values; h["la"]=ch.local_authority.values; h["lodgement_year"]=pd.to_datetime(ch.t).dt.year.values
    h.to_parquet(out,index=False); print(i,len(h),flush=True)
