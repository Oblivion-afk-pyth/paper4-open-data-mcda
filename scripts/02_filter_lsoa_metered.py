"""Extract Leeds rows (E08000035) from DESNZ LSOA domestic gas/electricity workbooks, 2019-2024 sheets."""
import openpyxl, pandas as pd
LA="E08000035"
cols=["la_code","la_name","msoa21cd","msoa_name","lsoa21cd","lsoa_name","n_meters","total_kwh","mean_kwh","median_kwh","n_nonconsuming"]
for fuel,f in [("gas","LSOA_domestic_gas_2010-2024.xlsx"),("elec","LSOA_domestic_elec_2010-2024.xlsx")]:
    wb=openpyxl.load_workbook("01_raw/metered_benchmark/"+f,read_only=True)
    out=[]
    for yr in ["2019","2020","2021","2022","2023","2024"]:
        for row in wb[yr].iter_rows(values_only=True):
            if row and row[0]==LA:
                r=list(row)[:len(cols)]+[None]*(len(cols)-len(row))
                out.append(r+[int(yr)])
    d=pd.DataFrame(out,columns=cols+["year"])
    d.to_csv(f"02_processed/leeds_lsoa_{fuel}_2019_2024.csv",index=False)
    print(fuel, d.groupby("year").agg(n=("lsoa21cd","nunique"),meters=("n_meters","sum"),mean_kwh=("mean_kwh","mean")).round(0).to_string())
