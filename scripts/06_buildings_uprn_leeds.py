"""Clip OS Open Map Local buildings (tile SE) and OS Open UPRN to Leeds LSOAs (EPSG:27700)."""
import zipfile, os, shutil, tempfile, geopandas as gpd, pandas as pd, sys
def save(g,path):
    t=os.path.join(tempfile.gettempdir(),os.path.basename(path))
    if os.path.exists(t): os.remove(t)
    g.to_file(t,driver="GPKG"); shutil.copyfile(t,path); os.remove(t)
step=sys.argv[1]
lsoa=gpd.read_file([f for f in os.listdir("01_raw/boundaries") if f.endswith(".gpkg")] and "01_raw/boundaries/"+[f for f in os.listdir("01_raw/boundaries") if f.endswith(".gpkg")][0])
lk=set(pd.read_csv("02_processed/leeds_postcode_lookup.csv",dtype=str).lsoa21cd)
code=[c for c in lsoa.columns if c.upper().startswith("LSOA21CD")][0]
lsoa=lsoa[lsoa[code].isin(lk)].to_crs(27700)[[code,"geometry"]].rename(columns={code:"lsoa21cd"})
save(lsoa,"02_processed/leeds_lsoa_2021.gpkg")
xmin,ymin,xmax,ymax=lsoa.total_bounds
if step=="bld":
    z=zipfile.ZipFile("01_raw/buildings/opmplc_essh_gb.zip")
    os.makedirs("01_raw/buildings/SE",exist_ok=True)
    for n in z.namelist():
        if n.startswith("data/SE/SE_Building."): 
            with open("01_raw/buildings/SE/"+os.path.basename(n),"wb") as f: f.write(z.read(n))
    b=gpd.read_file("01_raw/buildings/SE/SE_Building.shp",bbox=(xmin,ymin,xmax,ymax)).to_crs(27700)
    b["_x"]=b.geometry.centroid.x; b["_y"]=b.geometry.centroid.y
    pts=gpd.GeoDataFrame(b[["_x","_y"]],geometry=gpd.points_from_xy(b["_x"],b["_y"]),crs=27700)
    j=gpd.sjoin(pts,lsoa,predicate="within",how="inner")
    b=b.loc[j.index]; b["lsoa21cd"]=j["lsoa21cd"].values; b["footprint_m2"]=b.geometry.area
    save(b.drop(columns=["_x","_y"]),"02_processed/leeds_buildings_openmaplocal.gpkg")
    print("Leeds buildings:",len(b),"| median footprint m2:",round(b.footprint_m2.median(),1))
if step=="uprn":
    z=zipfile.ZipFile("01_raw/buildings/osopenuprn_202609_csv.zip")
    n=[x for x in z.namelist() if x.endswith(".csv")][0]; out=[]
    for ch in pd.read_csv(z.open(n),chunksize=2_000_000):
        out.append(ch[(ch.X_COORDINATE.between(xmin,xmax))&(ch.Y_COORDINATE.between(ymin,ymax))])
    u=pd.concat(out)
    g=gpd.GeoDataFrame(u,geometry=gpd.points_from_xy(u.X_COORDINATE,u.Y_COORDINATE),crs=27700)
    g=gpd.sjoin(g,lsoa,predicate="within",how="inner").drop(columns="index_right")
    g.drop(columns="geometry").to_csv("02_processed/leeds_uprn.csv",index=False)
    print("Leeds UPRNs:",len(g))
