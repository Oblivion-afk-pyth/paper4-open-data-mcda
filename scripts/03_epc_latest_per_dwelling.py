"""Combine Leeds EPC parts, keep the latest certificate per dwelling (UPRN; else address+postcode), attach LSOA via postcode."""
import pandas as pd, glob
parts=sorted(glob.glob("02_processed/epc_parts/certificates-*_leeds.csv"))
d=pd.concat((pd.read_csv(p,dtype=str,low_memory=False) for p in parts),ignore_index=True)
n_all=len(d)
d["lodgement_datetime"]=pd.to_datetime(d["lodgement_datetime"].fillna(d["lodgement_date"]),errors="coerce")
d["key"]=d["uprn"].where(d["uprn"].notna()&(d["uprn"]!=""), "ADDR|"+d["address"].str.upper().str.strip()+"|"+d["postcode"].str.upper().str.strip())
d=d.sort_values("lodgement_datetime").drop_duplicates("key",keep="last")
lk=pd.read_csv("02_processed/leeds_postcode_lookup.csv",dtype=str)[["pcds","oa21cd","lsoa21cd","msoa21cd"]]
d["pc"]=d["postcode"].str.upper().str.strip()
d=d.merge(lk,left_on="pc",right_on="pcds",how="left").drop(columns=["pcds","pc"])
d.to_csv("02_processed/epc_leeds_latest.csv",index=False)
print(f"certificates: {n_all:,} -> unique dwellings: {len(d):,}")
print("with UPRN: %.1f%%"%(100*(~d.key.str.startswith('ADDR')).mean()), "| matched to LSOA: %.1f%%"%(100*d.lsoa21cd.notna().mean()))
print("lodgement year of latest cert:\n", d.lodgement_datetime.dt.year.value_counts().sort_index().to_string())
print(d.property_type.value_counts().to_string()); print(d.current_energy_rating.value_counts().sort_index().to_string())
