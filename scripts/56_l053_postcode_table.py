"""Leeds 053 postcode table: proxy (T1, T1c) and metered-2024 energy, EPC fractions, costs, LSOA social criteria,
stock homogeneity, and BIM criteria (form factor, PV roof area). Definitions identical to script 36 (citywide LSOA table)."""
import os,numpy as np,pandas as pd,geopandas as gpd
D=(__import__("paths").ROOT+""); P=D+"02_processed/"; O=P+"v4_district/"
GAP={"A/B":0.0,"C":0.08,"D":0.20,"E":0.34,"F/G":0.48}
h=pd.read_csv(O+"l053_epc_linked.csv",low_memory=False)
h=h[h.lodgement_year<=2024].copy()
cost=pd.read_parquet(P+"v2/cert_costs_2024prices.parquet")["cost_2024"]
A=pd.read_csv(P+"v2/lsoa_table_v2.csv",index_col=0)
for k in ["gas","elec","total"]: A[f"f_{k}"]=A[f"proxyc_{k}_mean"]/A[f"proxy_{k}_mean"]
g=(h.MAIN_HEAT_FUEL==1)
h["save"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1); h["abate"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
h["att"]=1/(1+h.EPC.map(GAP)); h["save_att"]=h.save*h.att; h["abate_att"]=h.abate*h.att
h["cost"]=h.certificate_number.map(cost)
h["tot"]=h.pred_gas+h.pred_elec; h["gas_pg"]=h.pred_gas.where(g); h["is_gas"]=g.astype(float)
# T1c: LSOA area-correction factors (trained outside Leeds) applied to each dwelling
h["totc"]=h.tot*h.lsoa21cd.map(A.f_total); h["gasc_pg"]=h.gas_pg*h.lsoa21cd.map(A.f_gas); h["elecc"]=h.pred_elec*h.lsoa21cd.map(A.f_elec)
# BIM attributes per dwelling (via footprint bid)
b=gpd.read_file(O+"l053_buildings_v2.gpkg").drop(columns="geometry").set_index("bid")
h=h.join(b[["form_factor","pv_area_m2","n_epc","lidar_ok","exposed_wall_m2","roof_area_m2"]].rename(columns={"n_epc":"b_n_epc"}),on="bid")
ok=h.lidar_ok.fillna(False).astype(bool)
h["ff"]=h.form_factor.where(ok); h["pv_dw"]=(h.pv_area_m2/h.b_n_epc).where(ok)
h["arch"]=h.built_form.fillna(h.PROP_TYPE).astype(str)+"|"+h.PROP_AGE_BAND.astype(str)
cols=["tot","totc","gas_pg","gasc_pg","pred_elec","elecc","tfa_m2","is_gas","save","abate","save_att","abate_att","cost","epc_primary_kwh_m2","ff","pv_dw"]
T=h.groupby("postcode")[cols].mean()
# BIM criteria: postcode MEDIAN dwelling (robust to a few large multi-dwelling buildings), then winsorised 5/95% across kept postcodes below
T[["ff","pv_dw"]]=h.groupby("postcode")[["ff","pv_dw"]].median()
T["n_epc"]=h.groupby("postcode").size(); T["n_geom"]=h.groupby("postcode").ff.count()
T["lsoa21cd"]=h.groupby("postcode").lsoa21cd.agg(lambda s:s.mode().iat[0])
T["C6_stock_homogeneity"]=h.groupby("postcode").arch.agg(lambda s:s.value_counts().iat[0]/len(s)*100)
T=T.rename(columns={"tot":"proxy_total_mean","totc":"proxyc_total_mean","gas_pg":"proxy_gas_mean","gasc_pg":"proxyc_gas_mean","pred_elec":"proxy_elec_mean","elecc":"proxyc_elec_mean",
  "tfa_m2":"mean_tfa","is_gas":"gas_share_epc","cost":"pkg_cost_2024","epc_primary_kwh_m2":"mean_epc_primary","ff":"C7_form_factor","pv_dw":"C8_pv_area_dw"})
gm=pd.read_csv(P+"leeds_postcode_gas_2024.csv").set_index("Postcode"); em=pd.read_csv(P+"leeds_postcode_elec_2024.csv").set_index("Postcode")
T["gas_meters"]=gm.Num_meters; T["met_gas_mean"]=gm.Mean_cons_kwh; T["elec_meters"]=em.Num_meters; T["met_elec_mean"]=em.Mean_cons_kwh
T["met_gas_share"]=(T.gas_meters/T.elec_meters).clip(upper=1).fillna(0); T["met_total_mean"]=T.met_gas_mean.fillna(0)*T.met_gas_share+T.met_elec_mean
T["fuel_poverty_pct"]=T.lsoa21cd.map(A.fuel_poverty_pct); T["income_score"]=T.lsoa21cd.map(A.income_score)
T["coverage"]=T.n_epc/T.elec_meters
T["keep"]=T.met_elec_mean.notna()&T.met_gas_mean.notna()&(T.n_epc>=5)&(T.coverage>=0.5)&(T.n_geom>=3)
for c in ["C7_form_factor","C8_pv_area_dw"]:
    k=T.keep; lo,hi=T.loc[k,c].quantile([0.05,0.95]); T[c+"_raw"]=T[c]; T[c]=T[c].clip(lo,hi)
# postcode centroid from UPRN points (for spatial weights)
xy=h.groupby("postcode")[["X_COORDINATE","Y_COORDINATE"]].mean(); T["x"]=xy.X_COORDINATE; T["y"]=xy.Y_COORDINATE
T.to_csv(O+"l053_postcode_table.csv")
print("postcodes",len(T),"kept",int(T.keep.sum()),"dwellings in kept",int(T.loc[T.keep,"n_epc"].sum()))
print(T.loc[T.keep,["proxy_total_mean","proxyc_total_mean","met_total_mean","mean_tfa","C6_stock_homogeneity","C7_form_factor","C8_pv_area_dw","pkg_cost_2024","coverage"]].describe().round(2).T.to_string())
print(T[T.keep].groupby("lsoa21cd").size().to_dict())
