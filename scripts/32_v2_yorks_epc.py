"""v2: Yorkshire (excl. Leeds) latest EPC per dwelling lodged <= 2024-12-31; newest-first single pass (memory-light);
LSOA assigned via postcode (not LA code) so Barnsley, Sheffield and North Yorkshire are retained."""
import pandas as pd, glob, zipfile, os
CUT=pd.Timestamp("2024-12-31 23:59:59"); OUT="02_processed/v2/yorks_epc_latest_v2.csv"
parts=sorted(glob.glob("02_processed/yorks_parts/certificates-*_yorks.csv"),reverse=True)
parts=[p for p in parts if int(p.split("certificates-")[1][:4])<=2024]
seen=set(); first=True; n=0
for p in parts:
    d=pd.read_csv(p,dtype=str)
    d["t"]=pd.to_datetime(d.lodgement_datetime.fillna(d.lodgement_date),errors="coerce"); d=d[d.t<=CUT]
    d["key"]=d.uprn.where(d.uprn.notna(),"A|"+d.address.str.upper()+"|"+d.postcode.str.upper())
    d=d.sort_values("t",ascending=False).drop_duplicates("key"); d=d[~d.key.isin(seen)]
    seen.update(d.key); n+=len(d)
    d.drop(columns=["key"]).to_csv(OUT,mode="w" if first else "a",header=first,index=False); first=False
pcs=set(pd.read_csv(OUT,usecols=["postcode"],dtype=str).postcode.str.upper().str.strip())
z=zipfile.ZipFile("01_raw/boundaries/PCD_OA21_LSOA21_MSOA21_LAD_AUG23_UK_LU.zip")
lk=pd.concat(c[c.pcds.isin(pcs)] for c in pd.read_csv(z.open(z.namelist()[0]),usecols=["pcds","lsoa21cd","msoa21cd"],dtype=str,encoding="latin-1",chunksize=400_000))
lk.to_csv("02_processed/v2/yorks_postcode_lookup_v2.csv",index=False)
print("dwellings",n,"| postcodes matched",len(lk))
