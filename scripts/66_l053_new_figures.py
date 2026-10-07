"""New manuscript figures: (A) BIM derivation for a sample block, (B) 3D LOD1 district (IFC geometry: footprints extruded to eaves),
(C) criteria correlation + objective weights. Palette: validated default slots 1-2, single-hue blue ramp, blue-grey-orange diverging."""
import os,json,numpy as np,pandas as pd,geopandas as gpd,rasterio,matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.enums import Resampling
from rasterio.features import rasterize
from matplotlib.colors import LinearSegmentedColormap,ListedColormap,Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.geometry import box,Polygon,MultiPolygon
from shapely.ops import unary_union
D=(__import__("paths").ROOT+""); O=D+"02_processed/v4_district/"; OUT=D+"03_outputs/v4_district/"; F=OUT+"figures/"
S1,S2="#2a78d6","#eb6834"; INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; MUTED="#8f8e88"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK2,"ytick.color":INK2,
  "axes.spines.top":False,"axes.spines.right":False,"axes.axisbelow":True,"legend.frameon":False})
BLUE=LinearSegmentedColormap.from_list("b",["#e8f1fc","#9cc3f0","#2a78d6","#173f73"])
DIV=LinearSegmentedColormap.from_list("d",["#173f73","#2a78d6","#f2f1ee","#eb6834","#8a3412"])
def save(fig,n): fig.savefig(F+n+".png",dpi=300,bbox_inches="tight"); fig.savefig(F+n+".pdf",bbox_inches="tight"); plt.close(fig)
b=gpd.read_file(O+"l053_buildings_v2.gpkg"); b["geometry"]=b.geometry.force_2d()
def polys(g): return list(g.geoms) if isinstance(g,MultiPolygon) else [g]
def extrude(ax,gdf,hcol,cvals,cmap,norm,zscale=1.0,edge=(0.25,0.25,0.25,0.35),lw=0.15,x0=0,y0=0):
    faces=[];cols=[]
    for g,h,c in zip(gdf.geometry,gdf[hcol],cvals):
        if not np.isfinite(h) or h<=0: continue
        col=cmap(norm(c)); z=h*zscale
        for p in polys(g):
            xy=np.asarray(p.exterior.coords)[:,:2]-[x0,y0]
            faces.append([(x,y,z) for x,y in xy]); cols.append(col)
            sh=np.array(col); sh[:3]*=0.78
            for (xa,ya),(xb,yb) in zip(xy[:-1],xy[1:]):
                faces.append([(xa,ya,0),(xb,yb,0),(xb,yb,z),(xa,ya,z)]); cols.append(tuple(sh))
    pc=Poly3DCollection(faces,facecolors=cols,edgecolors=[edge],linewidths=lw,zsort="average"); ax.add_collection3d(pc)
# ================= Fig A: derivation steps for one block
ok=b[b.lidar_ok].copy(); c=ok.geometry.centroid
bb=ok[ok.built_form=="Enclosed Mid-Terrace"]
cnt=[(c.distance(g)<55).sum() for g in bb.geometry.centroid]
cx,cy=bb.geometry.centroid.iloc[int(np.argmax(cnt))].coords[0]
W,H=150,110; win=box(cx-W/2,cy-H/2,cx+W/2,cy+H/2)
sel=b[b.intersects(win)].copy(); sel["geometry"]=sel.geometry.intersection(win)
def mos(fs,B):
    Wd=int(B[2]-B[0]);Hd=int(B[3]-B[1]);T=from_origin(B[0],B[3],1,1);out=np.full((Hd,Wd),np.nan)
    for f in fs:
        with rasterio.open((__import__("paths").WORK+"r/")+f) as s:
            a=s.read(1).astype("float64"); a[a<-1e30]=np.nan; tmp=np.full((Hd,Wd),np.nan)
            reproject(a,tmp,src_transform=s.transform,src_crs=s.crs,dst_transform=T,dst_crs=s.crs,resampling=Resampling.bilinear,src_nodata=np.nan,dst_nodata=np.nan)
            out=np.where(np.isnan(out),tmp,out)
    return out,T
B=(np.floor(cx-W/2)-2,np.floor(cy-H/2)-2,np.ceil(cx+W/2)+2,np.ceil(cy+H/2)+2)
dsm,T=mos(["SE33sw_FZ_DSM_1m.tif","SE33nw_FZ_DSM_1m.tif"],B); dtm,_=mos(["SE33sw_DTM_2m.tif","SE33nw_DTM_2m.tif"],B)
nd=dsm-dtm; gy,gx=np.gradient(dsm); slope=np.degrees(np.arctan(np.hypot(gx,gy))); asp=(np.degrees(np.arctan2(-gx,gy))+360)%360
inb=rasterize([(g,1) for g in sel.geometry],out_shape=nd.shape,transform=T,fill=0)==1
roof=inb&(nd>2)
pv=roof&(((slope>=10)&(slope<=60)&(asp>=90)&(asp<=270))|(slope<10))
ext=(B[0],B[2],B[1],B[3])
fig=plt.figure(figsize=(7.6,6.4)); gs=fig.add_gridspec(2,2,hspace=0.38,wspace=0.08)
a=fig.add_subplot(gs[0,0]); im=a.imshow(np.clip(nd,0,14),extent=ext,cmap=BLUE,vmin=0,vmax=14,interpolation="nearest")
sel.boundary.plot(ax=a,color="white",lw=0.6)
cax_=a.inset_axes([0.0,-0.07,0.45,0.035]); cb=fig.colorbar(im,cax=cax_,orientation="horizontal"); cax_.text(1.04,0.5,"Height above ground (m)",transform=cax_.transAxes,va="center",fontsize=7.5,color=INK2); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
a.set_title("a  nDSM (DSM 1 m − DTM 2 m), footprints",loc="left",fontsize=8.5)
a2=fig.add_subplot(gs[0,1]); rgb=np.ones(nd.shape+(3,))*np.array([0.93,0.93,0.92])
rgb[roof]=matplotlib.colors.to_rgb("#9cc3f0"); rgb[pv]=matplotlib.colors.to_rgb(S2)
a2.imshow(rgb,extent=ext,interpolation="nearest"); sel.boundary.plot(ax=a2,color=INK2,lw=0.4)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
a2.legend(handles=[Patch(color=S2,label="PV-suitable roof pixel"),Patch(color="#9cc3f0",label="Other roof pixel")],loc="upper left",bbox_to_anchor=(0,-0.01),ncol=2,fontsize=7,handlelength=1)
a2.set_title("b  Roof slope and aspect → PV area (C8)",loc="left",fontsize=8.5)
a3=fig.add_subplot(gs[1,0]); sel.plot(ax=a3,color="#f2f1ee",lw=0)
geoms=list(sel.geometry); party=[];expo=[]
for i,g in enumerate(geoms):
    others=unary_union([h for j,h in enumerate(geoms) if j!=i and h.distance(g)<0.6]) if len(geoms)>1 else None
    bd=g.boundary
    if others is not None and not others.is_empty:
        buf=others.buffer(0.5); party.append(bd.intersection(buf)); expo.append(bd.difference(buf))
    else: expo.append(bd)
gpd.GeoSeries(expo).plot(ax=a3,color=S1,lw=1.1); gpd.GeoSeries(party).plot(ax=a3,color=S2,lw=1.1)
a3.legend(handles=[Line2D([],[],color=S1,lw=2,label="Exposed wall"),Line2D([],[],color=S2,lw=2,label="Party wall (≤ 0.5 m of neighbour)")],loc="upper left",bbox_to_anchor=(0,-0.01),ncol=2,fontsize=7,handlelength=1.5)
a3.set_title("c  Exposed and party walls → form factor (C7)",loc="left",fontsize=8.5)
for ax_ in (a,a2,a3): ax_.set_xlim(cx-W/2,cx+W/2); ax_.set_ylim(cy-H/2,cy+H/2); ax_.set_axis_off(); ax_.set_aspect("equal")
a.plot([cx-W/2+5,cx-W/2+55],[cy-H/2+4,cy-H/2+4],color=INK,lw=2.5); a.text(cx-W/2+30,cy-H/2+6,"50 m",color=INK,ha="center",va="bottom",fontsize=7.5,bbox=dict(fc="white",ec="none",pad=0.5))
a4=fig.add_subplot(gs[1,1],projection="3d"); s4=sel[sel.eaves_m.notna()]
ffn=Normalize(0.9,2.8); extrude(a4,s4,"eaves_m",s4.form_factor,BLUE,ffn,zscale=1.0,x0=cx,y0=cy)
a4.set_xlim(-W/2,W/2); a4.set_ylim(-H/2,H/2); a4.set_zlim(0,25); a4.set_box_aspect((W,H,25*1.6),zoom=1.25); a4.view_init(elev=32,azim=-58); a4.set_axis_off()
sm=plt.cm.ScalarMappable(cmap=BLUE,norm=ffn); cb=fig.colorbar(sm,ax=a4,shrink=0.55,pad=0.0); cb.set_label("Form factor",fontsize=7.5,color=INK2); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
a4.set_title("d  LOD1 IFC (extruded to eaves)",loc="left",fontsize=8.5)
save(fig,"Fig5_bim_derivation_block")
print("block",round(cx),round(cy),"buildings",len(sel),"roof px",int(roof.sum()),"pv px",int(pv.sum()))
# ================= Fig B: 3D district
d3=b[b.lidar_ok&b.eaves_m.notna()].copy(); x0,y0,x1,y1=d3.total_bounds; mx,my=(x0+x1)/2,(y0+y1)/2
fig=plt.figure(figsize=(8.6,4.8)); gs=fig.add_gridspec(3,2,width_ratios=[2.7,1],hspace=0.85,wspace=0.12)
ax=fig.add_subplot(gs[:,0],projection="3d")
ffv=d3.form_factor.clip(0.9,2.8); extrude(ax,d3,"eaves_m",ffv,BLUE,ffn,zscale=1.0,edge=(0.2,0.2,0.2,0.25),lw=0.05,x0=mx,y0=my)
Wx,Wy=x1-x0,y1-y0; ax.set_xlim(-Wx/2,Wx/2); ax.set_ylim(-Wy/2,Wy/2); ax.set_zlim(0,40); ax.set_box_aspect((Wx,Wy,40*2),zoom=1.4); ax.view_init(elev=38,azim=-62); ax.set_axis_off()
ax.set_title(f"a  Leeds 053 LOD1 model, {len(d3):,} buildings (heights ×2)",loc="left",fontsize=9,y=0.98)
sm=plt.cm.ScalarMappable(cmap=BLUE,norm=ffn); cax2=ax.inset_axes([0.18,0.04,0.4,0.03]); cb=fig.colorbar(sm,cax=cax2,orientation="horizontal"); cb.set_label("Form factor (heat-loss area ÷ floor area)",fontsize=7.5,color=INK2); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
pw=(d3.party_wall_len_m/d3.perim_m).clip(0,1)*100
for k,(v,lab,bins) in enumerate([(d3.eaves_m.clip(0,15),"Eaves height (m)",np.arange(0,15.5,0.5)),(pw,"Party-wall share of perimeter (%)",np.arange(0,101,4)),(d3.form_factor.clip(0,4),"Form factor",np.arange(0,4.01,0.1))]):
    h=fig.add_subplot(gs[k,1]); v=v.dropna(); h.hist(v,bins=bins,color=S1,edgecolor="white",linewidth=0.4)
    h.axvline(np.median(v),color=S2,lw=1.4); h.set_xlabel(lab,fontsize=7.5); h.tick_params(labelsize=7); h.set_yticks([])
    h.spines["left"].set_visible(False); h.text(0.02 if k==1 else 0.98,0.92,f"median {np.median(v):.1f}",transform=h.transAxes,ha="left" if k==1 else "right",va="top",fontsize=7,color=INK2)
    if k==0: h.set_title("b  Distributions",loc="left",fontsize=9)
save(fig,"Fig7_district_lod1_3d")
print("3d",len(d3),"median eaves",round(d3.eaves_m.median(),1),"pw",round(pw.median(),1),"ff",round(d3.form_factor.median(),2))
# ================= Fig C: correlation + weights
C=pd.read_csv(OUT+"l053_criteria_corr_spearman.csv",index_col=0); lab=["C1 energy int.","C2 carbon","C3 fuel poverty","C4 income depr.","C5 cost-eff.","C6 homogeneity","C7 form factor","C8 PV area"]
fig,(a,bx)=plt.subplots(1,2,figsize=(8.0,3.6),gridspec_kw={"width_ratios":[1.15,1]}); fig.subplots_adjust(wspace=0.55)
M=C.values.copy(); mask=np.triu(np.ones_like(M,bool),k=0); Mm=np.ma.array(M,mask=mask)
im=a.imshow(Mm,cmap=DIV,vmin=-1,vmax=1)
for i in range(8):
    for j in range(i):
        a.text(j,i,f"{M[i,j]:.2f}".replace("-0.00","0.00"),ha="center",va="center",fontsize=6.8,color="white" if abs(M[i,j])>0.55 else INK)
a.set_xticks(range(7)); a.set_xticklabels(lab[:7],rotation=45,ha="right",fontsize=7); a.set_yticks(range(1,8)); a.set_yticklabels(lab[1:],fontsize=7)
a.set_xlim(-0.5,6.5); a.set_ylim(7.5,0.5); a.grid(False)
for s in a.spines.values(): s.set_visible(False)
for k in (6,7):
    a.add_patch(plt.Rectangle((-0.5,k-0.5),k,1,fill=False,ec=S2,lw=1.2))
cb=fig.colorbar(im,ax=a,shrink=0.7,pad=0.03); cb.set_label("Spearman ρ (81 postcodes)",fontsize=7.5,color=INK2); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
a.set_title("a  Correlation between criteria",loc="left",fontsize=9,pad=20)
Wv=json.load(open(OUT+"l053_weight_vectors.json")); w6=Wv["T1c six criteria|objective"]; w8=Wv["T1c eight criteria|objective"]
keys=list(w8); y=np.arange(len(keys))
v6=[w6.get(k,np.nan) for k in keys]; v8=[w8[k] for k in keys]
bx.barh(y-0.19,v6,height=0.36,color=S1,label="Six criteria"); bx.barh(y+0.19,v8,height=0.36,color=S2,label="Eight criteria (+ BIM)")
for yy,v in zip(y,v6):
    if v==v: bx.text(v+0.005,yy-0.19,f"{v:.2f}",va="center",fontsize=6.8,color=INK2)
for yy,v in zip(y,v8): bx.text(v+0.005,yy+0.19,f"{v:.2f}",va="center",fontsize=6.8,color=INK2)
bx.set_yticks(y); bx.set_yticklabels(lab,fontsize=7); bx.invert_yaxis(); bx.set_xlim(0,0.42); bx.set_xlabel("Objective weight (entropy–CRITIC)",fontsize=8)
bx.grid(axis="x",color=GRID,lw=0.6); bx.legend(loc="lower left",bbox_to_anchor=(0,1.0),ncol=2,fontsize=7.5); bx.tick_params(labelsize=7)
bx.set_title("b  Data-driven weights",loc="left",fontsize=9,pad=20)
save(fig,"Fig10_criteria_corr_weights")
print("weights8",w8)
