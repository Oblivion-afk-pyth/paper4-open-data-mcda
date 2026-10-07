import os,numpy as np,geopandas as gpd,pandas as pd,rasterio
from rasterio.merge import merge
from rasterio.features import rasterize
from rasterio.enums import Resampling
D=(__import__("paths").ROOT+"")
fp=gpd.read_file(D+"02_processed/v4_district/l053_plot_footprints.gpkg").reset_index(drop=True)
fp["bid"]=np.arange(len(fp))
x0,y0,x1,y1=fp.total_bounds; B=(np.floor(x0)-20,np.floor(y0)-20,np.ceil(x1)+20,np.ceil(y1)+20)
def mos(fs,res):
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    W=int(B[2]-B[0]); H=int(B[3]-B[1]); T=from_origin(B[0],B[3],1,1); out=np.full((H,W),np.nan)
    for f in fs:
        with rasterio.open((__import__("paths").WORK+"r/")+f) as s:
            a=s.read(1).astype("float64"); a[a<-1e30]=np.nan; tmp=np.full((H,W),np.nan)
            reproject(a,tmp,src_transform=s.transform,src_crs=s.crs,dst_transform=T,dst_crs=s.crs,resampling=Resampling.bilinear,src_nodata=np.nan,dst_nodata=np.nan)
            out=np.where(np.isnan(out),tmp,out)
    return out,T
dsm,T=mos(["SE33sw_FZ_DSM_1m.tif","SE33nw_FZ_DSM_1m.tif"],1)
dtm,_=mos(["SE33sw_DTM_2m.tif","SE33nw_DTM_2m.tif"],1)
ndsm=dsm-dtm
gy,gx=np.gradient(dsm,1.0); slope=np.degrees(np.arctan(np.hypot(gx,gy)))
aspect=(np.degrees(np.arctan2(-gx,gy))+360)%360  # 0=N, clockwise (rows go south)
lab=rasterize(((g,i+1) for g,i in zip(fp.geometry,fp.bid)),out_shape=dsm.shape,transform=T,fill=0,all_touched=False,dtype="int32")
df=pd.DataFrame({"b":lab.ravel()-1,"h":ndsm.ravel(),"s":slope.ravel(),"a":aspect.ravel(),"g":dtm.ravel()}); df=df[df.b>=0]
roofpx=df[df.h>2.0]
south=roofpx[(roofpx.s.between(10,60))&((roofpx.a>=90)&(roofpx.a<=270))]
flat=roofpx[roofpx.s<10]
q=df.groupby("b").agg(n_px=("h","size"),h_p95=("h",lambda v:np.nanpercentile(v,95)),h_med=("h","median"),ground_m=("g","median"))
q["roof_px"]=roofpx.groupby("b").size(); q["roof_slope_med"]=roofpx.groupby("b").s.median()
q["pv_px"]=south.groupby("b").size().add(flat.groupby("b").size(),fill_value=0)
q["pv_area_m2"]=(south.assign(f=1/np.cos(np.radians(south.s))).groupby("b").f.sum()).add(flat.groupby("b").size(),fill_value=0)
fp=fp.join(q,on="bid")
# geometry
fp["area_m2"]=fp.area; fp["perim_m"]=fp.length
sidx=fp.sindex; shared=np.zeros(len(fp))
for i,g in enumerate(fp.geometry):
    gb=g.boundary
    for j in sidx.query(g.buffer(0.5)):
        if j==i: continue
        shared[i]+=gb.intersection(fp.geometry.iloc[j].buffer(0.5)).length
fp["party_wall_len_m"]=np.minimum(shared,fp.perim_m); fp["exposed_perim_m"]=fp.perim_m-fp.party_wall_len_m
fp["height_m"]=fp.h_p95; fp["eaves_m"]=fp.h_med.clip(lower=2.5)
fp["storeys_est"]=np.clip(np.round(fp.eaves_m/2.8),1,None)
fp["exposed_wall_m2"]=fp.exposed_perim_m*fp.eaves_m; fp["party_wall_m2"]=fp.party_wall_len_m*fp.eaves_m
fp["roof_area_m2"]=fp.area_m2/np.cos(np.radians(fp.roof_slope_med.fillna(0).clip(upper=60)))
fp["floor_area_est_m2"]=fp.area_m2*fp.storeys_est
fp["heat_loss_area_m2"]=fp.exposed_wall_m2+fp.roof_area_m2+fp.area_m2
fp["form_factor"]=fp.heat_loss_area_m2/fp.floor_area_est_m2
fp["volume_m3"]=fp.area_m2*fp.h_med.clip(lower=0)
fp["lidar_ok"]=(fp.roof_px/fp.n_px>0.5)&(fp.height_m>2.5)
fp.to_file("l053_buildings_geom.gpkg"); import shutil; shutil.copy("l053_buildings_geom.gpkg",D+"02_processed/v4_district/l053_buildings_geom.gpkg")
c=["area_m2","height_m","eaves_m","storeys_est","party_wall_len_m","exposed_wall_m2","roof_area_m2","pv_area_m2","form_factor"]
print(len(fp),"lidar_ok",fp.lidar_ok.sum()); print(fp.loc[fp.lidar_ok,c].describe(percentiles=[.1,.5,.9]).round(1).T.to_string())
print("share with party wall >0:",(fp.party_wall_len_m>1).mean().round(3))
