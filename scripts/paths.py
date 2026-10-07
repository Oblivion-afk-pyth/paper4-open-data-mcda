"""Central paths. Run every script from the repository root, e.g. `python scripts/57_l053_validation.py`.
ROOT  : repository root holding 01_raw/, 02_processed/, 03_outputs/, models/ (override with PAPER4_DATA)
WORK  : local scratch for unzipped rasters, GML and temporary GeoPackage/IFC files (override with PAPER4_WORK)
PAPER : folder for manuscript-related outputs (override with PAPER4_MANUSCRIPT)"""
import os
ROOT=os.path.abspath(os.environ.get("PAPER4_DATA",os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")))+os.sep
WORK=os.path.abspath(os.environ.get("PAPER4_WORK",os.path.join(ROOT,"_work")))+os.sep
PAPER=os.path.abspath(os.environ.get("PAPER4_MANUSCRIPT",os.path.join(ROOT,"manuscript")))+os.sep
for _d in (WORK,WORK+"r",WORK+"b"): os.makedirs(_d,exist_ok=True)
