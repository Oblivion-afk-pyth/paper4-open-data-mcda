"""Keep EPC recommendations for Leeds' latest certificates. Resumable per source file; run until ALL DONE."""
import zipfile, io, csv, os, sys, time, pandas as pd
Z="01_raw/epc/domestic-csv.zip"; P="02_processed/epc_parts/"; BUDGET=float(sys.argv[1]) if len(sys.argv)>1 else 150
csv.field_size_limit(10**8); t0=time.time()
keep=set(pd.read_csv("02_processed/epc_leeds_latest.csv",usecols=["certificate_number"],dtype=str).certificate_number)
z=zipfile.ZipFile(Z)
for n in sorted(x for x in z.namelist() if x.startswith("recommendations-")):
    out=P+n.replace(".csv","_leeds.csv")
    if os.path.exists(out): continue
    if time.time()-t0 + z.getinfo(n).file_size/40e6 > BUDGET and time.time()-t0>1: print("stop; budget"); break
    k=0
    with z.open(n) as f, open(out+".tmp","w",newline="",encoding="utf-8") as fo:
        r=csv.reader(io.TextIOWrapper(f,encoding="utf-8",errors="replace")); w=csv.writer(fo)
        h=next(r); i=h.index("certificate_number"); w.writerow(h)
        for row in r:
            if len(row)>i and row[i] in keep: w.writerow(row); k+=1
    os.replace(out+".tmp",out); print(f"{n}: {k:,}  t={time.time()-t0:.0f}s",flush=True)
left=[x for x in z.namelist() if x.startswith("recommendations-") and not os.path.exists(P+x.replace(".csv","_leeds.csv"))]
print("remaining:",len(left),"ALL DONE" if not left else "")
