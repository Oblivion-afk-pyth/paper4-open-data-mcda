import zipfile,laspy,numpy as np,glob,os,io,sys,json
src=(__import__("paths").ROOT+"01_raw/lidar")
out={}
cells=set()
for zf in sorted(glob.glob(src+"/*.zip")):
    if os.path.getsize(zf)==0: continue
    z=zipfile.ZipFile(zf)
    for n in z.namelist():
        p=os.path.join("laz",n)
        if not os.path.exists(p): z.extract(n,"laz")
        with laspy.open(p) as f:
            h=f.header; cnt=h.point_count
            for pts in f.chunk_iterator(5_000_000):
                x=np.floor(np.asarray(pts.x)/10).astype(np.int64); y=np.floor(np.asarray(pts.y)/10).astype(np.int64)
                cells.update(set(zip(x.tolist()[::1],y.tolist()[::1])) if False else set(map(tuple,np.unique(np.c_[x,y],axis=0).tolist())))
            out[n]=dict(points=int(cnt),mins=list(h.mins),maxs=list(h.maxs),crs=str(h.parse_crs()) [:60] if h.parse_crs() else None)
        print(n,cnt,h.mins[:2],h.maxs[:2],flush=True)
np.save((__import__("paths").ROOT+"03_outputs/v4_district/lidar_cells10m.npy"),np.array(sorted(cells)))
json.dump(out,open((__import__("paths").ROOT+"03_outputs/v4_district/lidar_tiles.json"),"w"),indent=1)
print("cells",len(cells),"area km2",len(cells)*100/1e6)
