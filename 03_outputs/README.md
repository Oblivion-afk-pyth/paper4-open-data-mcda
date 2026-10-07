# Outputs

| Folder / file | Content | Paper |
|---|---|---|
| `v2/matrix_leeds_*.csv`, `v2/matrix_bradford_*.csv` | LSOA decision matrices: meter-informed reference T0, proxies T1, T1c, tiers T2–T4 and variants (`_att`, `_c1total`) | Sections 3.7, 4.1 |
| `v2/level1_v2.json`, `v2/correction_validation.json` | Prediction validation and area-correction cross-validation | Tables 9–10 |
| `v2/decision_validation_v2.csv`, `v2/bootstrap_ci_v2.json`, `v2/threshold_grid_v2.csv`, `v2/weight_vectors_v2.json` | Decision agreement under each weighting and method, intervals, thresholds, weights | Tables 11–13, S3–S7 |
| `v2/montecarlo_*`, `v2/spatial_v2.json`, `v2/rq4_*` | Monte Carlo misplacement, Moran's I, OLS/spatial error model | Tables S8–S9 |
| `v2/tiers_v2.csv`, `v2/noepc_*`, `v2/checks_v3.*` | Data-reduction tiers, models without EPC rating, robustness checks | Tables S6, S6a, S10 |
| `v2/figures/` | City-stage figures | Figs. 2–4, S1–S6 |
| `v4_district/msoa_inventory.csv` | Leeds MSOAs: certificates, meters, footprints, LiDAR coverage (district selection) | Section 3.16 |
| `v4_district/l053_matrix_*.csv`, `l053_criteria_corr_spearman.csv` | Postcode decision matrices (C1–C8) and criteria correlation | Section 4.5–4.6 |
| `v4_district/l053_validation.json`, `l053_decision_validation.csv`, `l053_weight_vectors.json` | District prediction and decision validation | Tables 14–15 |
| `v4_district/l053_noise_mc_spatial.json`, `l053_montecarlo_ptop20.csv` | Meter-noise ceiling, Monte Carlo, Moran's I | Sections 4.4, 4.7 |
| `v4_district/leeds_outside_postcodes_pred_vs_met.csv` | Predicted vs metered energy for 11,741 Leeds postcodes outside the district | Fig. 8a |
| `v4_district/l053_building_scores.csv` | Building-level GRA scores and ranks (illustrative) | Section 4.8 |
| `v4_district/Leeds053_LOD1.ifc`, `Leeds053_LOD1_priority.ifc` | IFC4 LOD1 model without / with priority property set | Sections 3.16, 4.2, 4.8 |
| `v4_district/figures/` | District figures, workflow diagram, graphical abstract | Figs. 1, 5–11 |
| top-level files and `figures/` | First-version (superseded) outputs from `scripts/legacy/` | – |
