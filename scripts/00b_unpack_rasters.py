"""Unpack the EA LiDAR DSM (1 m) and DTM (2 m) tiles covering Leeds 053 into the scratch folder used by scripts 53, 54 and 66."""
import os,glob,zipfile
from paths import ROOT,WORK
TILES=["SE33sw","SE33nw"]
for sub in ["dsm_1m_2022","dtm_2m_2022"]:
    for t in TILES:
        zs=glob.glob(os.path.join(ROOT,"01_raw","lidar",sub,f"*{t}.zip"))
        if not zs: print("missing",sub,t,"- see DATA_SOURCES.md"); continue
        with zipfile.ZipFile(zs[0]) as z:
            for n in z.namelist():
                if n.endswith((".tif",".tfw")): z.extract(n,WORK+"r"); print("unpacked",n)
