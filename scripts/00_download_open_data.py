"""Download the open inputs that have a stable direct link into 01_raw/ (run from the repository root).
Datasets that need a sign-in or an interactive download (EPC register, ONS boundary files, Census bulk tables,
OS Open Map Local / Open UPRN, EA LiDAR tiles) are listed in DATA_SOURCES.md and must be fetched manually."""
import os,sys,requests
from paths import ROOT
FILES={
 "need/anon2026_4million.zip":"https://assets.publishing.service.gov.uk/media/6a38ed076422bec01b1178a9/anon2026_4million.zip",
 "need/NEED-2026-anonymised-dataset-metadata.ods":"https://assets.publishing.service.gov.uk/media/6a282d2be371d9d2c0052b39/NEED-2026-anonymised-dataset-metadata.ods",
 "metered_benchmark/LSOA_domestic_gas_2010-2024.xlsx":"https://assets.publishing.service.gov.uk/media/694578171a2e540ccd8a5426/LSOA_domestic_gas_2010-2024.xlsx",
 "metered_benchmark/LSOA_domestic_elec_2010-2024.xlsx":"https://assets.publishing.service.gov.uk/media/69427b7bd8156a816c419351/LSOA_domestic_elec_2010-2024.xlsx",
 "metered_benchmark/Postcode_level_gas_2024.csv":"https://assets.publishing.service.gov.uk/media/6942a4e2501cdd438f4cf502/Postcode_level_gas_2024.csv",
 "metered_benchmark/Postcode_level_all_meters_electricity_2024.csv":"https://assets.publishing.service.gov.uk/media/694282a1fdbd8404f9e1f1da/Postcode_level_all_meters_electricity_2024.csv",
 "fuel_poverty/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx":"https://assets.publishing.service.gov.uk/media/6a02febf81a251700a20b42a/fuel-poverty-sub-regional-2026-2024-data-tables.xlsx",
 "deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv":"https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",
 "buildings/inspire/Leeds_City_Council.zip":"https://use-land-property-data.service.gov.uk/datasets/inspire/download/Leeds_City_Council.zip",
}
for rel,url in FILES.items():
    out=os.path.join(ROOT,"01_raw",rel)
    if os.path.exists(out): print("exists  ",rel); continue
    os.makedirs(os.path.dirname(out),exist_ok=True); print("download",rel)
    try:
        with requests.get(url,stream=True,timeout=120) as r:
            r.raise_for_status()
            with open(out+".part","wb") as f:
                for ch in r.iter_content(1<<20): f.write(ch)
        os.replace(out+".part",out)
    except Exception as e: print("  failed:",e,"- download manually from",url,file=sys.stderr)
print("Manual downloads still needed: see DATA_SOURCES.md")
