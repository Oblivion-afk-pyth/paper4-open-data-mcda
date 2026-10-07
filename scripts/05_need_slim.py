"""Slim NEED 2026 4M sample to modelling columns (features + 2023/2024 consumption and validity flags) -> parquet."""
import zipfile, pandas as pd
feat=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","CONSERVATORY_FLAG","COUNCIL_TAX_BAND","IMD_BAND_ENG","REGION","EPC","LI_FLAG","CWI_FLAG","PV_FLAG","MAIN_HEAT_FUEL"]
tgt=["Gcons2024","GasValFlag2024","Econs2024","ElecValFlag2024","Gcons2023","GasValFlag2023","Econs2023","ElecValFlag2023"]
z=zipfile.ZipFile("01_raw/need/anon2026_4million.zip")
parts=[]
for ch in pd.read_csv(z.open("anon2026_4million.csv"),usecols=feat+tgt,chunksize=500_000,low_memory=False):
    ch=ch[ch.REGION.str.startswith("E")]           # England only (IoD 2025 England quintiles)
    parts.append(ch)
d=pd.concat(parts,ignore_index=True)
for c in ["PROP_TYPE","COUNCIL_TAX_BAND","REGION","EPC","GasValFlag2024","ElecValFlag2024","GasValFlag2023","ElecValFlag2023"]: d[c]=d[c].astype("category")
d.to_parquet("02_processed/need2026_england_slim.parquet",index=False)
print(d.shape); print(d.REGION.value_counts().to_string())
print("Yorkshire & Humber:",(d.REGION=="E12000003").sum())
print("gas valid 2024: %.1f%%"%(100*(d.GasValFlag2024=="V").mean()),"| elec valid 2024: %.1f%%"%(100*(d.ElecValFlag2024=="V").mean()))
