"""Stream the national domestic EPC zip and keep Leeds (E08000035) certificates.
Resumable: writes one part file per source year; skips parts already done. Run repeatedly until it prints ALL DONE."""
import zipfile, io, csv, os, sys, time
LA="E08000035"; Z="01_raw/epc/domestic-csv.zip"; P="02_processed/epc_parts/"
BUDGET=float(sys.argv[1]) if len(sys.argv)>1 else 150
csv.field_size_limit(10**8)
z=zipfile.ZipFile(Z); t0=time.time()
todo=[n for n in sorted(z.namelist()) if n.startswith("certificates-") and not os.path.exists(P+n.replace(".csv","_leeds.csv"))]
for n in todo:
    size=z.getinfo(n).file_size
    if time.time()-t0 + size/45e6 > BUDGET and time.time()-t0>1: print("stop; budget"); break
    tmp=P+n.replace(".csv","_leeds.tmp"); k=tot=0
    with z.open(n) as f, open(tmp,"w",newline="",encoding="utf-8") as fo:
        r=csv.reader(io.TextIOWrapper(f,encoding="utf-8",errors="replace")); w=csv.writer(fo)
        h=next(r); ila=h.index("local_authority"); w.writerow(h)
        for row in r:
            tot+=1
            if len(row)>ila and row[ila]==LA: w.writerow(row); k+=1
    os.replace(tmp,P+n.replace(".csv","_leeds.csv"))
    print(f"{n}: {k:,} Leeds / {tot:,}  t={time.time()-t0:.0f}s",flush=True)
left=[n for n in z.namelist() if n.startswith("certificates-") and not os.path.exists(P+n.replace(".csv","_leeds.csv"))]
print("remaining:",len(left)); print("ALL DONE" if not left else "")
