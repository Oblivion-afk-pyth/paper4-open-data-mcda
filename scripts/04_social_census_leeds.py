"""Leeds LSOA tables: fuel poverty 2024, IoD 2025, Census 2021 (TS017 household size, TS054 tenure, TS052 occupancy)."""
import openpyxl, pandas as pd, zipfile
LA="E08000035"
# fuel poverty Table 4
ws=openpyxl.load_workbook("01_raw/fuel_poverty/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx",read_only=True)["Table 4"]
rows=[r[:8] for r in ws.iter_rows(min_row=4,values_only=True) if r[2]==LA]
fp=pd.DataFrame(rows,columns=["lsoa21cd","lsoa_name","la_code","la_name","region","fp_households","fp_fuel_poor","fp_pct"])
fp.to_csv("02_processed/leeds_lsoa_fuel_poverty_2024.csv",index=False); print("fuel poverty LSOAs:",len(fp))
# IoD
iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv")
iod=iod[iod["Local Authority District code (2024)"]==LA]
iod.to_csv("02_processed/leeds_lsoa_iod2025.csv",index=False); print("IoD LSOAs:",len(iod))
# census
lsoas=set(fp.lsoa21cd)
for t in ["ts017","ts054","ts052"]:
    z=zipfile.ZipFile(f"01_raw/census/census2021-{t}.zip")
    n=[x for x in z.namelist() if x.endswith("-lsoa.csv")][0]
    c=pd.read_csv(z.open(n))
    code=[k for k in c.columns if "code" in k.lower()][0]
    c=c[c[code].isin(lsoas)]
    c.to_csv(f"02_processed/leeds_lsoa_census_{t}.csv",index=False)
    print(t,len(c),"LSOAs;",len(c.columns),"cols; e.g.",list(c.columns)[3:6])
