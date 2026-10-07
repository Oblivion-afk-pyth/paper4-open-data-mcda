"""v2: EPC recommendations for Leeds v2 and Yorkshire v2 certificates (cert, improvement_id, cost). Resumable per source file."""
import zipfile, io, csv, os, sys, time, pandas as pd
P="02_processed/v2/recs_parts/"; BUDGET=float(sys.argv[1]); t0=time.time(); csv.field_size_limit(10**8)
KF=P+"_keep.txt"
if not os.path.exists(KF):
    k=set(pd.read_parquet("02_processed/v2/leeds_epc_harmonised_v2.parquet",columns=["certificate_number"]).certificate_number)
    k|=set(pd.read_csv("02_processed/v2/yorks_epc_latest_v2.csv",usecols=["certificate_number"],dtype=str).certificate_number)
    open(KF,"w").write("\n".join(k))
keep=set(open(KF).read().split("\n")); z=zipfile.ZipFile("01_raw/epc/domestic-csv.zip")
for n in sorted(x for x in z.namelist() if x.startswith("recommendations-")):
    out=P+n.replace(".csv","_v2.csv")
    if os.path.exists(out): continue
    if time.time()-t0+z.getinfo(n).file_size/40e6>BUDGET and time.time()-t0>1: print("stop"); break
    k=0
    with z.open(n) as f, open(out+".tmp","w",newline="") as fo:
        r=csv.reader(io.TextIOWrapper(f,encoding="utf-8",errors="replace")); h=next(r)
        ic,ii,ico=h.index("certificate_number"),h.index("improvement_id"),h.index("indicative_cost"); w=csv.writer(fo); w.writerow(["certificate_number","improvement_id","indicative_cost"])
        for row in r:
            if len(row)>ico and row[ic] in keep: w.writerow([row[ic],row[ii],row[ico]]); k+=1
    os.replace(out+".tmp",out); print(n,k,f"{time.time()-t0:.0f}s",flush=True)
left=[x for x in z.namelist() if x.startswith("recommendations-") and not os.path.exists(P+x.replace(".csv","_v2.csv"))]; print("remaining",len(left))
