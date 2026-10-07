"""Yorkshire (excl. Leeds) calibration set: NEED-model proxy per LSOA."""
import pandas as pd, sys
sys.path.insert(0,"scripts"); from harmonise import *
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",usecols=[0,6])
dec=iod.set_index(iod.columns[0])[iod.columns[1]]
USE=["certificate_number","lsoa21cd","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential"]
e=pd.read_csv("02_processed/yorks_epc_latest.csv",usecols=USE,dtype=str)
A=lsoa_aggregate(predict(harmonise(e,dec)))
A.to_csv("02_processed/yorks_lsoa_proxy.csv"); print(A.shape); print(A.describe().round(1).T[["mean","min","max"]].to_string())
