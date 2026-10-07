"""Yorkshire (excl. Leeds): latest EPC per dwelling + LSOA, memory-light two-pass."""
import pandas as pd, glob, zipfile
LAS={"E06000010","E06000011","E06000012","E06000013","E06000014","E06000065","E08000017","E08000018","E08000032","E08000033","E08000034","E08000036","E08000038","E08000039"}
parts=sorted(glob.glob("02_processed/yorks_parts/certificates-*_yorks.csv"))
K=pd.concat((pd.read_csv(p,usecols=["certificate_number","uprn","address","postcode","lodgement_datetime","lodgement_date"],dtype=str) for p in parts),ignore_index=True)
n=len(K)
K["t"]=pd.to_datetime(K.lodgement_datetime.fillna(K.lodgement_date),errors="coerce")
K["key"]=K.uprn.where(K.uprn.notna(),"A|"+K.address.str.upper()+"|"+K.postcode.str.upper())
keep=set(K.sort_values("t").drop_duplicates("key",keep="last").certificate_number); del K
out=[]
for p in parts:
    d=pd.read_csv(p,dtype=str); out.append(d[d.certificate_number.isin(keep)])
E=pd.concat(out,ignore_index=True)
z=zipfile.ZipFile("01_raw/boundaries/PCD_OA21_LSOA21_MSOA21_LAD_AUG23_UK_LU.zip")
lk=pd.concat(c[c.ladcd.isin(LAS)] for c in pd.read_csv(z.open(z.namelist()[0]),usecols=["pcds","lsoa21cd","ladcd"],dtype=str,encoding="latin-1",chunksize=500_000))
E["pc"]=E.postcode.str.upper().str.strip()
E=E.merge(lk.rename(columns={"pcds":"pc"}),on="pc",how="left")
E=E[E.lsoa21cd.notna()]
E.to_csv("02_processed/yorks_epc_latest.csv",index=False)
print(f"certs {n:,} -> dwellings with LSOA {len(E):,}; LSOAs {E.lsoa21cd.nunique():,}; LAs {E.local_authority.nunique()}")
