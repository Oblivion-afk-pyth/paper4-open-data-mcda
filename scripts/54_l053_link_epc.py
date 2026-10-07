# Leeds 053: refine eaves height and link EPC dwellings (UPRN points) to plot footprints
import os,shutil,numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.enums import Resampling
from rasterio.features import rasterize
D=(__import__("paths").ROOT+""); P=D+"02_processed/"; R=(__import__("paths").WORK+"r/")
fp=gpd.read_file(P+"v4_district/l053_buildings_geom.gpkg")
x0,y0,x1,y1=fp.total_bounds; B=(np.floor(x0)-20,np.floor(y0)-20,np.ceil(x1)+20,np.ceil(y1)+20)
W=int(B[2]-B[0]); H=int(B[3]-B[1]); T=from_origin(B[0],B[3],1,1)
def mos(fs):
    out=np.full((H,W),np.nan)
    for f in fs:
        with rasterio.open(R+f) as s:
            a=s.read(1).astype("float64"); a[a<-1e30]=np.nan; tmp=np.full((H,W),np.nan)
            reproject(a,tmp,src_transform=s.transform,src_crs=s.crs,dst_transform=T,dst_crs=s.crs,resampling=Resampling.bilinear,src_nodata=np.nan,dst_nodata=np.nan)
            out=np.where(np.isnan(out),tmp,out)
    return out
ndsm=mos(["SE33sw_FZ_DSM_1m.tif","SE33nw_FZ_DSM_1m.tif"])-mos(["SE33sw_DTM_2m.tif","SE33nw_DTM_2m.tif"])
# party walls: shared boundary with the UNION of neighbouring footprints (no double counting at corners)
sidx=fp.sindex; shared=[]
for i,g in enumerate(fp.geometry):
    nb=[j for j in sidx.query(g.buffer(0.5)) if j!=i]
    shared.append(g.boundary.intersection(fp.geometry.iloc[nb].buffer(0.5).union_all()).length if nb else 0.0)
fp["party_wall_len_m"]=np.minimum(shared,fp.perim_m); fp["exposed_perim_m"]=fp.perim_m-fp.party_wall_len_m
# eaves = ridge - run*tan(pitch); run = footprint extent along dominant down-slope direction,
# halved when the roof is dual-pitched (aspect vectors cancel, low resultant length)
dsm=mos(["SE33sw_FZ_DSM_1m.tif","SE33nw_FZ_DSM_1m.tif"]); gy,gx=np.gradient(dsm)
gy=-gy  # rows run north->south
slope=np.degrees(np.arctan(np.hypot(gx,gy))); ux=-gx/np.hypot(gx,gy); uy=-gy/np.hypot(gx,gy)  # downslope unit vector (E,N)
lab=rasterize(((g,i+1) for i,g in enumerate(fp.geometry)),out_shape=(H,W),transform=T,fill=0,dtype="int32")
df=pd.DataFrame({"b":lab.ravel()-1,"h":ndsm.ravel(),"s":slope.ravel(),"ux":ux.ravel(),"uy":uy.ravel()})
df=df[(df.b>=0)&(df.h>2)&(df.s.between(10,65))]
agg=df.groupby("b").agg(ux=("ux","mean"),uy=("uy","mean"),pitch=("s","median"),npx=("s","size"))
agg["R"]=np.hypot(agg.ux,agg.uy)
import shapely
runs=[];
for b,r in agg.iterrows():
    g=fp.geometry.iloc[b]; d=np.array([r.ux,r.uy])/max(r.R,1e-9)
    if r.R<0.35:  # dual pitch: use axial direction from doubled angles
        sub=df[df.b==b]; th=np.arctan2(sub.uy,sub.ux)*2; m=np.arctan2(np.sin(th).mean(),np.cos(th).mean())/2; d=np.array([np.cos(m),np.sin(m)])
    xy=np.asarray(g.exterior.coords) if g.geom_type=="Polygon" else np.vstack([np.asarray(p.exterior.coords) for p in g.geoms])
    L=np.ptp(xy[:,:2]@d); runs.append(L if r.R>=0.35 else L/2)
agg["run_m"]=runs
fp=fp.join(agg[["pitch","R","run_m"]].rename(columns={"pitch":"roof_pitch_deg","R":"aspect_R"}))
rise=fp.run_m*np.tan(np.radians(fp.roof_pitch_deg.clip(upper=55)))
fp["eaves_m"]=np.where(fp.roof_pitch_deg.notna(),(fp.height_m-rise).clip(lower=2.5),fp.height_m)
fp["eaves_m"]=np.minimum(fp.eaves_m,fp.height_m)
fp["exposed_wall_m2"]=fp.exposed_perim_m*fp.eaves_m; fp["party_wall_m2"]=fp.party_wall_len_m*fp.eaves_m
fp["storeys_est"]=np.clip(np.round(fp.eaves_m/2.7),1,None)
# EPC link via UPRN coordinates
ep=pd.read_parquet(P+"v2/leeds_dwelling_predictions_v2.parquet")
ep=ep[ep.msoa21cd=="E02002382"].copy(); ep["uprn"]=pd.to_numeric(ep.uprn,errors="coerce")
import glob
UC=["certificate_number","postcode","built_form","floor_height","number_habitable_rooms","roof_description","walls_description","tenure"]
raw=pd.concat((pd.read_csv(f,dtype=str,usecols=UC) for f in sorted(glob.glob(P+"epc_parts/certificates-*_leeds.csv")) if "(1)" not in f),ignore_index=True)
raw=raw[raw.certificate_number.isin(set(ep.certificate_number))].drop_duplicates("certificate_number")
raw["floor_height"]=pd.to_numeric(raw.floor_height,errors="coerce"); raw["number_habitable_rooms"]=pd.to_numeric(raw.number_habitable_rooms,errors="coerce")
raw["postcode"]=raw.postcode.str.upper().str.strip()
ep=ep.merge(raw,on="certificate_number",how="left")
up=pd.read_csv(P+"leeds_uprn.csv",usecols=["UPRN","X_COORDINATE","Y_COORDINATE"])
ep=ep.merge(up,left_on="uprn",right_on="UPRN",how="left")
pts=gpd.GeoDataFrame(ep,geometry=gpd.points_from_xy(ep.X_COORDINATE,ep.Y_COORDINATE),crs=27700)
fp["bid"]=np.arange(len(fp))
j=gpd.sjoin(pts[pts.X_COORDINATE.notna()],fp[["bid","geometry"]],predicate="within",how="left")
# unmatched points: nearest footprint within 8 m (address point on pavement/yard)
um=j.bid.isna(); 
if um.any():
    nn=gpd.sjoin_nearest(pts.loc[j.index[um]].drop(columns=[c for c in ["index_right","bid"] if c in pts]),fp[["bid","geometry"]],max_distance=8,how="left")
    j.loc[um,"bid"]=nn.groupby(level=0).bid.first().reindex(j.index[um]).values
j["link"]=np.where(um,np.where(j.bid.notna(),"nearest<=8m","none"),"within")
j=j.drop(columns=["geometry","index_right"],errors="ignore")
j.to_csv(D+"02_processed/v4_district/l053_epc_linked.csv",index=False)
g=j[j.bid.notna()].groupby("bid").agg(n_epc=("certificate_number","size"),epc_tfa_m2=("tfa_m2","sum"),
    prop_type=("PROP_TYPE",lambda s:s.mode().iat[0]),built_form=("built_form",lambda s:s.mode().iat[0] if s.notna().any() else None),
    epc_band=("EPC",lambda s:s.mode().iat[0]),age_band=("PROP_AGE_BAND",lambda s:s.mode().iat[0]),
    epc_kwh_m2=("epc_primary_kwh_m2","mean"),pred_gas_kwh=("pred_gas","sum"),pred_elec_kwh=("pred_elec","sum"),
    postcode=("postcode",lambda s:s.mode().iat[0] if s.notna().any() else None),floor_height_m=("floor_height","median"))
fp=fp.drop(columns=[c for c in g.columns if c in fp],errors="ignore").join(g,on="bid")
fp["n_epc"]=fp.n_epc.fillna(0).astype(int)
fp["floor_area_m2"]=fp.epc_tfa_m2.where(fp.n_epc>0,fp.area_m2*fp.storeys_est)
fp["floor_area_src"]=np.where(fp.n_epc>0,"EPC","geometry")
fp["heat_loss_area_m2"]=fp.exposed_wall_m2+fp.roof_area_m2+fp.area_m2
fp.loc[fp.floor_area_m2<=0,"floor_area_m2"]=np.nan
fp["form_factor"]=fp.heat_loss_area_m2/fp.floor_area_m2
fp.to_file((__import__("paths").WORK+"l053_buildings_v2.gpkg")); shutil.copy((__import__("paths").WORK+"l053_buildings_v2.gpkg"),P+"v4_district/l053_buildings_v2.gpkg")
print("EPC rows",len(ep),"with coords",ep.X_COORDINATE.notna().sum()); print(j.link.value_counts())
print("footprints with EPC",(fp.n_epc>0).sum(),"of",len(fp)); print(fp.n_epc.value_counts().sort_index().head(8))
ok=fp[fp.lidar_ok&(fp.n_epc==1)]
print(ok[["area_m2","height_m","eaves_m","storeys_est","exposed_wall_m2","party_wall_m2","roof_area_m2","pv_area_m2","epc_tfa_m2","form_factor","roof_pitch_deg","run_m"]].describe(percentiles=[.1,.5,.9]).round(1).T.to_string())
print("TFA vs footprint ratio median:",(ok.epc_tfa_m2/ok.area_m2).median().round(2)); print(ok.built_form.value_counts().head(6))
