"""Stream national EPCs; keep Yorkshire & Humber LAs except Leeds (calibration region), modelling columns only. Resumable."""
import zipfile, io, csv, os, sys, time
LAS={"E06000010","E06000011","E06000012","E06000013","E06000014","E06000065","E08000017","E08000018","E08000032","E08000033","E08000034","E08000036","E08000038","E08000039"}
USE=["certificate_number","uprn","address","postcode","local_authority","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential","lodgement_datetime","lodgement_date"]
Z="01_raw/epc/domestic-csv.zip"; P="02_processed/yorks_parts/"; BUDGET=float(sys.argv[1]); t0=time.time()
csv.field_size_limit(10**8); z=zipfile.ZipFile(Z)
for n in sorted(x for x in z.namelist() if x.startswith("certificates-")):
    out=P+n.replace(".csv","_yorks.csv")
    if os.path.exists(out): continue
    if time.time()-t0+z.getinfo(n).file_size/45e6>BUDGET and time.time()-t0>1: print("stop; budget"); break
    k=0
    with z.open(n) as f, open(out+".tmp","w",newline="",encoding="utf-8") as fo:
        r=csv.reader(io.TextIOWrapper(f,encoding="utf-8",errors="replace")); h=next(r); idx=[h.index(c) for c in USE]; ila=h.index("local_authority")
        w=csv.writer(fo); w.writerow(USE)
        for row in r:
            if len(row)>ila and row[ila] in LAS: w.writerow([row[i] for i in idx]); k+=1
    os.replace(out+".tmp",out); print(f"{n}: {k:,} t={time.time()-t0:.0f}s",flush=True)
left=[x for x in z.namelist() if x.startswith("certificates-") and not os.path.exists(P+x.replace(".csv","_yorks.csv"))]
print("remaining",len(left))
