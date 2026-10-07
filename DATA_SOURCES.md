# Data sources

All inputs are open. Save each file in the folder shown, keeping the original file name (scripts expect these names). Links checked 24 September and 6 October 2026. Files marked **auto** are fetched by `python scripts/00_download_open_data.py`.

## City stage

| Dataset | Save to | Source | Licence |
|---|---|---|---|
| NEED anonymised 2026, 4 million records (`anon2026_4million.zip`) **auto** | `01_raw/need/` | https://www.gov.uk/government/collections/national-energy-efficiency-data-framework-need | OGL v3 |
| NEED 2026 metadata (`NEED-2026-anonymised-dataset-metadata.ods`) **auto** | `01_raw/need/` | as above | OGL v3 |
| Domestic EPCs, England and Wales (`domestic-csv.zip`; sign in with GOV.UK One Login, Domestic, all of England and Wales or by authority) | `01_raw/epc/` | https://get-energy-performance-data.communities.gov.uk/ | OGL v3 (address data subject to Royal Mail and OS rights) |
| LSOA domestic gas and electricity 2010–2024 (`LSOA_domestic_gas_2010-2024.xlsx`, `LSOA_domestic_elec_2010-2024.xlsx`) **auto** | `01_raw/metered_benchmark/` | https://www.gov.uk/government/collections/sub-national-gas-consumption-data, https://www.gov.uk/government/collections/sub-national-electricity-consumption-data | OGL v3 |
| Postcode-level domestic gas and electricity 2024 (`Postcode_level_gas_2024.csv`, `Postcode_level_all_meters_electricity_2024.csv`) **auto** | `01_raw/metered_benchmark/` | as above | OGL v3 |
| Sub-regional fuel poverty 2026, 2024 data (`fuel-poverty-sub-regional-2026-2024-data-tables.xlsx`) **auto** | `01_raw/fuel_poverty/` | https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2026-2024-data | OGL v3 |
| English Indices of Deprivation 2025, File 7 (`File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv`) **auto** | `01_raw/deprivation/` | https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025 | OGL v3 |
| Postcode to OA (2021) to LSOA to MSOA to LAD best-fit lookup, August 2023 (`PCD_OA21_LSOA21_MSOA21_LAD_AUG23_UK_LU.zip`) | `01_raw/boundaries/` | https://geoportal.statistics.gov.uk/datasets/3770c5e8b0c24f1dbe6d2fc6b46a0b18 | OGL v3 |
| LSOA December 2021 boundaries EW BSC V4 (GeoPackage) | `01_raw/boundaries/` | https://geoportal.statistics.gov.uk/datasets/lower-layer-super-output-areas-december-2021-boundaries-ew-bsc-v4-2 | OGL v3 |
| Census 2021 bulk tables TS017, TS052, TS054 (`census2021-ts0xx.zip`) | `01_raw/census/` | https://www.nomisweb.co.uk/sources/census_2021_bulk | OGL v3 |
| ONS CPIH index (series L522) – values are entered in `scripts/34_v2_costs.py` | – | https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/l522/mm23 | OGL v3 |

## District stage (Leeds MSOA 053, E02002382)

| Dataset | Save to | Source | Licence |
|---|---|---|---|
| HM Land Registry INSPIRE Index Polygons, Leeds (`Leeds_City_Council.zip`) **auto** | `01_raw/buildings/inspire/` | https://use-land-property-data.service.gov.uk/datasets/inspire/download | HM Land Registry INSPIRE download licence |
| OS Open Map Local, GB, ESRI Shapefile (`opmplc_essh_gb.zip`; script 06 extracts tile SE) | `01_raw/buildings/` | https://osdatahub.os.uk/downloads/open/OpenMapLocal | OGL v3 |
| OS Open UPRN, CSV (`osopenuprn_202609_csv.zip`; edit the name in scripts 06 and 52 for later releases) | `01_raw/buildings/` | https://osdatahub.os.uk/downloads/open/OpenUPRN | OGL v3 |
| EA LIDAR Composite First Return DSM 1 m 2022, tiles SE33sw and SE33nw (`lidar_composite_first_return_dsm-2022-1-SE33sw.zip`, …) | `01_raw/lidar/dsm_1m_2022/` | https://environment.data.gov.uk/survey | OGL v3 |
| EA LIDAR Composite DTM 2 m 2022, tiles SE33sw and SE33nw (`lidar_composite_dtm-2022-2-SE33sw.zip`, …) | `01_raw/lidar/dtm_2m_2022/` | https://environment.data.gov.uk/survey | OGL v3 |
| OpenStreetMap West Yorkshire extract (`west-yorkshire-*-free.gpkg.zip`) – used only to compare footprint sources in script 52 | `01_raw/buildings/osm/` | https://download.geofabrik.de/europe/united-kingdom/england/west-yorkshire.html | ODbL |

Script 50 (district selection) also reads EA LiDAR point-cloud tiles; it is not needed to reproduce the district results.
