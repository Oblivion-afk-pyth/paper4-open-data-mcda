# Data-efficient MCDA for district renovation: open-data BIM and AI without local metered energy data

Code, derived results and the open-data BIM (IFC) model for the paper

> Wimalasena, S., Turskis, Z., Šliogerienė, J. *Data-Efficient Multi-Criteria Decision Analysis for District Renovation: Bridging Open-Data BIM and AI Without Local Metered Energy Data.* Manuscript submitted to the *Journal of Cleaner Production* (2026).

The study ranks renovation priorities twice with the same MCDA pipeline – once with open-data proxies and once with a meter-informed reference built from DESNZ 2024 consumption – and measures how far the decisions agree:

- **City scale (Leeds, 488 LSOAs; Bradford as geographical holdout).** Dwelling energy is estimated by models trained on the national NEED sample and transferred to the local EPC stock (T1), with an optional area-level correction learned from other Yorkshire authorities (T1c).
- **District scale (Leeds MSOA 053, 81 postcodes, 2,711 buildings).** An LOD1 building model is derived from HM Land Registry INSPIRE polygons, OS Open Map Local and Environment Agency LiDAR, exported to IFC4, and adds two geometry criteria (form factor C7, PV-suitable roof area C8).

No local metered data enter the proxy rankings; meters are used only to build the reference and to validate.

## Repository layout

```
scripts/            numbered pipeline (run in order from the repository root) + shared modules
  paths.py          central paths (override with PAPER4_DATA / PAPER4_WORK)
  harmonise.py      EPC-to-NEED feature mapping and prediction
  mcda.py, mcda_v2.py  weighting (entropy, CRITIC, combined), GRA, TOPSIS, VIKOR, agreement statistics
  legacy/           superseded first-version scripts (10–20, 22–26), kept for provenance only
01_raw/             raw downloads – NOT included; see DATA_SOURCES.md
02_processed/       intermediate tables – generated; only the district postcode table is included
03_outputs/         results and figures (city stage in 03_outputs/v2, district stage in 03_outputs/v4_district)
models/             trained LightGBM transfer and tier models (text format) and their metrics
```

## Installation

Python 3.10 (tested with 3.10.12).

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducing the results

1. Download the open datasets into `01_raw/` as described in [DATA_SOURCES.md](DATA_SOURCES.md). Files with a direct link can be fetched with `python scripts/00_download_open_data.py`; the EPC register (GOV.UK One Login), OS products, LiDAR tiles and the ONS boundary files are downloaded manually.
2. Unpack the LiDAR tiles for the district: `python scripts/00b_unpack_rasters.py`.
3. Run the scripts in numerical order from the repository root, e.g. `python scripts/30_v2_leeds_epc.py`.

| Scripts | Stage | Main outputs |
|---|---|---|
| 01–07 | Extract Leeds EPCs, meters, census and social tables; slim NEED sample; coverage check | `02_processed/` |
| 08, 09, 21 | Harmonise EPC to NEED features; train transfer (gas, electricity) and tier models | `models/`; Tables S1–S2 |
| 30–36 | Leeds and Yorkshire certificates (≤ 2024), recommendations, costs, LSOA table | `02_processed/v2/` |
| 37 | Area-level correction (random, leave-one-authority-out and spatial-block validation) | T1c; Table 10 |
| 38–43 | Decision matrices, prediction and decision validation, Monte Carlo, spatial models, tiers, figures | `03_outputs/v2/`; Tables 9, 11–13, S3–S10; Figs. 2–4, S1–S6 |
| 44–46 | Models without the EPC rating; robustness checks | Table S6, S6a |
| 50–51 | LiDAR coverage and MSOA inventory (district selection) | `03_outputs/v4_district/msoa_inventory.csv` |
| 52–55 | Plot footprints, LiDAR geometry, party walls/eaves, EPC linkage, IFC4 export | `Leeds053_LOD1.ifc` |
| 56–59 | Postcode criteria, district validation, noise ceiling, Monte Carlo, building scores | Tables 14–15; `Leeds053_LOD1_priority.ifc` |
| 60, 63–66 | District figures, workflow diagram, graphical abstract | Figs. 1, 5–11 |

Random seeds: transfer models 42, tier models 7, correction model and CV splits 1, Monte Carlo 2026, bootstrap 11.

Large intermediate files (unzipped rasters, GML) are written to `_work/` (or `$PAPER4_WORK`), which is git-ignored.

## The IFC model

`03_outputs/v4_district/Leeds053_LOD1_priority.ifc` (IFC4, georeferenced with `IfcMapConversion` to EPSG:27700) holds one `IfcBuilding` per plot footprint, extruded to eaves height, with three property sets:

| Property set | Content |
|---|---|
| `Pset_Paper4_Geometry` | footprint, perimeter, ridge and eaves height, roof pitch, party-wall length/area, exposed wall, roof and heat-loss area, form factor, PV-suitable roof area, LiDAR validity |
| `Pset_Paper4_EPC` | linked certificate attributes (property type, built form, age band, band, floor area, primary energy), postcode, predicted gas and electricity |
| `Pset_Paper4_Priority` | GRA score and building rank, postcode rank and Monte Carlo probability of being in the top quintile |

Building-level priorities are illustrative: they are not validated against meters, which exist only at postcode level. The file opens in any IFC viewer (e.g. BIMvision, Bonsai/BlenderBIM, IfcOpenShell).

## Licences

- Code (`scripts/`): MIT – see [LICENSE](LICENSE).
- Derived data, figures, models and the IFC model (`03_outputs/`, `02_processed/`, `models/`): CC BY 4.0 – see [LICENSE-DATA.md](LICENSE-DATA.md), which also lists the attribution statements required by the underlying open datasets.

## Citation

See [CITATION.cff](CITATION.cff). Please cite the paper once published.
