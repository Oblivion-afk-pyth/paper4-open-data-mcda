import pandas as pd,numpy as np,geopandas as gpd,os
D=(__import__("paths").ROOT+""); P=D+"02_processed/"
lk=pd.read_csv(P+"leeds_postcode_lookup.csv",usecols=["pcds","doterm","lsoa21cd","msoa21cd","msoa21nm","ladcd"],encoding="latin1")
lk=lk[lk.ladcd=="E08000035"]
lsoa2msoa=lk.drop_duplicates("lsoa21cd").set_index("lsoa21cd")[["msoa21cd","msoa21nm"]]
live=lk[lk.doterm.isna()]
# meters
gas=pd.read_csv(P+"leeds_postcode_gas_2024.csv"); el=pd.read_csv(P+"leeds_postcode_elec_2024.csv")
m=live[["pcds","msoa21cd"]].copy()
m["gas"]=m.pcds.isin(set(gas.Postcode)); m["el"]=m.pcds.isin(set(el.Postcode)); m["both"]=m.gas&m.el
g2=gas.merge(lk[["pcds","msoa21cd"]],left_on="Postcode",right_on="pcds"); e2=el.merge(lk[["pcds","msoa21cd"]],left_on="Postcode",right_on="pcds")
pc=m.groupby("msoa21cd").agg(postcodes_live=("pcds","size"),pc_gas=("gas","sum"),pc_elec=("el","sum"),pc_both=("both","sum"))
pc["gas_meters"]=g2.groupby("msoa21cd").Num_meters.sum(); pc["elec_meters"]=e2.groupby("msoa21cd").Num_meters.sum()
# EPC
ep=pd.read_parquet(P+"v2/leeds_epc_harmonised_v2.parquet",columns=["lsoa21cd","uprn","lodgement_year","PROP_TYPE"])
ep["msoa21cd"]=ep.lsoa21cd.map(lsoa2msoa.msoa21cd)
up=pd.read_csv(P+"leeds_uprn.csv",usecols=["UPRN","X_COORDINATE","Y_COORDINATE"])
ep["uprn"]=pd.to_numeric(ep.uprn,errors="coerce").astype("Int64"); up["UPRN"]=up.UPRN.astype("Int64")
ep=ep.merge(up,left_on="uprn",right_on="UPRN",how="left")
cells=np.load(D+"03_outputs/v4_district/lidar_cells10m.npy"); cs=set(map(tuple,cells.tolist()))
def cov(x,y):
    ok=~(np.isnan(x)|np.isnan(y)); r=np.zeros(len(x),bool)
    r[ok]=[(a,b) in cs for a,b in zip(np.floor(x[ok]/10).astype(int),np.floor(y[ok]/10).astype(int))]; return r
ep["xy"]=ep.X_COORDINATE.notna(); ep["lidar"]=cov(ep.X_COORDINATE.values,ep.Y_COORDINATE.values)
ep["le2024"]=ep.lodgement_year<=2024
ep["flat"]=ep.PROP_TYPE.astype(str).str.contains("flat|Flat|maison",regex=True)
ee=ep.groupby("msoa21cd").agg(epc_dw=("lsoa21cd","size"),epc_le2024=("le2024","sum"),epc_uprn_xy=("xy","sum"),epc_in_lidar=("lidar","sum"),pct_flat=("flat","mean"))
# footprints
b=gpd.read_file(P+"leeds_buildings_openmaplocal.gpkg")
c=b.geometry.centroid; b["lidar"]=cov(c.x.values,c.y.values); b["msoa21cd"]=b.lsoa21cd.map(lsoa2msoa.msoa21cd)
bb=b.groupby("msoa21cd").agg(footprints=("ID","size"),fp_in_lidar=("lidar","sum"),fp_area_m2=("footprint_m2","sum"))
# area + lidar area share
l=gpd.read_file(P+"leeds_lsoa_2021.gpkg"); l["msoa21cd"]=l.lsoa21cd.map(lsoa2msoa.msoa21cd)
ms=l.dissolve("msoa21cd"); ms["area_km2"]=ms.area/1e6
cg=gpd.GeoDataFrame(geometry=gpd.points_from_xy(cells[:,0]*10+5,cells[:,1]*10+5),crs=27700)
j=gpd.sjoin(cg,ms[["geometry"]].reset_index(),predicate="within")
ms["lidar_km2"]=j.groupby("msoa21cd").size()*100/1e6
# households
hh=pd.read_csv(P+"leeds_lsoa_census_ts017.csv").iloc[:,[2,3]]; hh.columns=["lsoa21cd","hh_spaces"]
hh["msoa21cd"]=hh.lsoa21cd.map(lsoa2msoa.msoa21cd)
# priority
mc=pd.read_csv(D+"03_outputs/v2/montecarlo_ptop20_v2.csv"); mc["msoa21cd"]=mc.lsoa21cd.map(lsoa2msoa.msoa21cd)
pr=mc.groupby("msoa21cd").agg(n_lsoa=("lsoa21cd","size"),mean_Ptop20=("objective|B_empirical_iid","mean"),lsoa_Ptop20_gt50=("objective|B_empirical_iid",lambda s:(s>0.5).sum()))
T=lsoa2msoa.drop_duplicates().set_index("msoa21cd").join([pr,hh.groupby("msoa21cd").hh_spaces.sum(),ee,pc,bb,ms[["area_km2","lidar_km2"]]])
T=T.fillna({"lidar_km2":0,"epc_in_lidar":0,"fp_in_lidar":0})
T["pct_area_lidar"]=100*T.lidar_km2/T.area_km2; T["pct_epc_lidar"]=100*T.epc_in_lidar/T.epc_dw; T["pct_fp_lidar"]=100*T.fp_in_lidar/T.footprints
T["epc_cov_pct"]=100*T.epc_dw/T.hh_spaces; T["pc_both_pct"]=100*T.pc_both/T.postcodes_live
T=T.round(3).sort_values("msoa21nm"); T.to_csv(D+"03_outputs/v4_district/msoa_inventory.csv")
print(T.sort_values("pct_epc_lidar",ascending=False).head(12).to_string())
print(T.loc[T.msoa21nm.isin(["Leeds 053"])].T.to_string())
print(T.sort_values("mean_Ptop20",ascending=False).head(12)[["msoa21nm","mean_Ptop20","hh_spaces","epc_dw","pc_both","footprints","pct_epc_lidar"]].to_string())
