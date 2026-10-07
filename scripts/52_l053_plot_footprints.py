import zipfile,os,pandas as pd,geopandas as gpd,numpy as np
D=(__import__("paths").ROOT+""); P=D+"02_processed/"; R=D+"01_raw/buildings/"
lk=pd.read_csv(P+"leeds_postcode_lookup.csv",usecols=["lsoa21cd","msoa21cd"]).drop_duplicates("lsoa21cd")
ls=lk[lk.msoa21cd=="E02002382"].lsoa21cd.tolist()
l=gpd.read_file(P+"leeds_lsoa_2021.gpkg"); dist=l[l.lsoa21cd.isin(ls)].dissolve().geometry.iloc[0]
bb=dist.buffer(50).bounds
if not os.path.exists((__import__("paths").WORK+"b/")+"parcels.gml"):
    with zipfile.ZipFile(R+"inspire/Leeds_City_Council.zip") as z, open((__import__("paths").WORK+"b/")+"parcels.gml","wb") as o: o.write(z.read("Land_Registry_Cadastral_Parcels.gml"))
ins=gpd.read_file((__import__("paths").WORK+"b/")+"parcels.gml",bbox=bb); ins=ins.set_crs(27700,allow_override=True)
ins=ins[ins.representative_point().within(dist)]
if not os.path.exists((__import__("paths").WORK+"b/")+"wy.gpkg"):
    with zipfile.ZipFile(R+"osm/west-yorkshire-261005-free.gpkg.zip") as z, open((__import__("paths").WORK+"b/")+"wy.gpkg","wb") as o: o.write(z.read("west-yorkshire.gpkg"))
import pyogrio; print(pyogrio.list_layers((__import__("paths").WORK+"b/")+"wy.gpkg"))
lay=[n for n,_ in pyogrio.list_layers((__import__("paths").WORK+"b/")+"wy.gpkg") if "building" in n][0]
osm=gpd.read_file((__import__("paths").WORK+"b/")+"wy.gpkg",layer=lay).to_crs(27700); osm=osm[osm.representative_point().within(dist)]
oml=gpd.read_file(P+"leeds_buildings_openmaplocal.gpkg",bbox=bb); oml=oml[oml.representative_point().within(dist)]
up=pd.read_csv(P+"leeds_uprn.csv"); ep=pd.read_parquet(P+"v2/leeds_epc_harmonised_v2.parquet",columns=["uprn","msoa21cd","PROP_TYPE"])
ep=ep[ep.msoa21cd=="E02002382"]; ep["uprn"]=pd.to_numeric(ep.uprn,errors="coerce")
e=ep.merge(up,left_on="uprn",right_on="UPRN"); eg=gpd.GeoDataFrame(e,geometry=gpd.points_from_xy(e.X_COORDINATE,e.Y_COORDINATE),crs=27700)
def stats(name,g):
    g=g.reset_index(drop=True); j=gpd.sjoin(eg,g[["geometry"]],predicate="within"); c=j.groupby("index_right").size()
    print(f"{name}: polygons {len(g)}, median area {g.area.median():.0f} m2, EPC pts inside any {len(j)}/{len(eg)}, polys with 1 EPC {(c==1).sum()}, 2-3 {((c>1)&(c<4)).sum()}, >=4 {(c>=4).sum()}, EPC in 1:1 polys {c[c==1].sum()}")
stats("OS OML",oml); stats("OSM",osm); stats("INSPIRE",ins)
# INSPIRE x OML intersection = per-plot building footprint
x=gpd.overlay(ins[["gml_id","geometry"]] if "gml_id" in ins else ins[["geometry"]],oml[["ID","geometry"]],how="intersection"); x=x[x.area>15]
stats("INSPIRE∩OML",x)
x.to_file(D+"02_processed/v4_district/l053_plot_footprints.gpkg")
