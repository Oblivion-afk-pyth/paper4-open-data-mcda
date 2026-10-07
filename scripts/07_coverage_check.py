"""Per-LSOA coverage: EPC dwellings vs census households and meter counts."""
import pandas as pd
e=pd.read_csv("02_processed/epc_leeds_latest.csv",usecols=["lsoa21cd","current_energy_rating","lodgement_datetime"],dtype=str)
e["recent"]=pd.to_datetime(e.lodgement_datetime,errors="coerce").dt.year>=2016
g=e.groupby("lsoa21cd").agg(epc_dwellings=("current_energy_rating","size"),epc_recent10y=("recent","sum"))
c=pd.read_csv("02_processed/leeds_lsoa_census_ts054.csv"); code=[k for k in c.columns if "code" in k.lower()][0]
c=c.rename(columns={code:"lsoa21cd"}).set_index("lsoa21cd")[["Tenure of household: Total: All households"]].rename(columns=lambda _:"households_2021")
el=pd.read_csv("02_processed/leeds_lsoa_elec_2019_2024.csv").query("year==2024").set_index("lsoa21cd")[["n_meters"]].rename(columns={"n_meters":"elec_meters_2024"})
ga=pd.read_csv("02_processed/leeds_lsoa_gas_2019_2024.csv").query("year==2024").set_index("lsoa21cd")[["n_meters"]].rename(columns={"n_meters":"gas_meters_2024"})
d=c.join([g,el,ga]); d["epc_coverage"]=d.epc_dwellings/d.households_2021; d["gas_share"]=d.gas_meters_2024/d.elec_meters_2024
d.to_csv("03_outputs/lsoa_coverage_check.csv")
print(d[["households_2021","epc_dwellings","elec_meters_2024","gas_meters_2024"]].sum().to_string())
print(d[["epc_coverage","gas_share"]].describe(percentiles=[.05,.25,.5,.75,.95]).round(2).to_string())
print("LSOAs with EPC coverage <50%:",(d.epc_coverage<0.5).sum(), "| >100%:",(d.epc_coverage>1).sum())
