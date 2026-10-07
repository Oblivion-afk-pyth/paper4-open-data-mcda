"""Graphical abstract (Elsevier: >= 1328 x 531 px, w x h). City priority map -> district LOD1 BIM -> key result."""
import os,json,numpy as np,pandas as pd,geopandas as gpd,matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
D=(__import__("paths").ROOT+""); OUT=D+"03_outputs/v4_district/figures/"
plt.rcParams.update({"font.family":"Liberation Sans"})
INK="#1f2937"; INK2="#4b5563"; S1="#2a78d6"; S2="#eb6834"; GREEN="#3f7d3a"
BLUE=LinearSegmentedColormap.from_list("b",["#eef4fc","#9cc3f0","#2a78d6","#173f73"])
ORNG=LinearSegmentedColormap.from_list("o",["#fdf0e6","#f6b386","#eb6834","#8a3412"])
V=json.load(open(D+"03_outputs/v4_district/l053_validation.json")); N=json.load(open(D+"03_outputs/v4_district/l053_noise_mc_spatial.json"))
l=gpd.read_file(D+"02_processed/leeds_lsoa_2021.gpkg"); mc=pd.read_csv(D+"03_outputs/v2/montecarlo_ptop20_v2.csv",index_col=0)
l["p"]=l.lsoa21cd.map(mc["equal|C_empirical_spatial"])
d053=l[l.lsoa21cd.isin(["E01011430","E01011432","E01011433","E01011434"])].dissolve()
b=gpd.read_file(D+"02_processed/v4_district/l053_buildings_v2.gpkg"); b=b[b.lidar_ok.astype(bool)]
fig=plt.figure(figsize=(13.28,5.31)); W,H=13.28,5.31
def ax_at(x,y,w,h): a=fig.add_axes([x/W,y/H,w/W,h/H]); a.set_axis_off(); return a
fig.text(0.25/W,(H-0.38)/H,"Two targeting decisions, validated against 2024 meter data (Leeds, UK)",fontsize=17,fontweight="bold",color=INK,va="center")
# panel 1
fig.text(0.35/W,(H-0.95)/H,"1  City: which neighbourhoods?",fontsize=14,fontweight="bold",color=S1,va="center")
a1=ax_at(0.2,0.75,3.9,3.55); l.plot(ax=a1,column="p",cmap=BLUE,vmin=0,vmax=1,linewidth=0.15,edgecolor="white"); d053.boundary.plot(ax=a1,color=S2,linewidth=2.2); a1.set_aspect("equal")
c=d053.geometry.iloc[0].centroid; a1.annotate("Leeds 053",xy=(c.x,c.y),xytext=(c.x+5500,c.y+6500),fontsize=11,color=S2,fontweight="bold",arrowprops=dict(arrowstyle="-",color=S2,lw=1.2))
fig.text(0.35/W,0.42/H,"488 neighbourhoods · open data vs meters:\nρ = 0.91 (equal weights) · MAPE 6.2%",fontsize=11.5,color=INK2,va="center",linespacing=1.35)
# arrow
fig.patches.append(FancyArrowPatch((4.25/W,2.6/H),(4.85/W,2.6/H),transform=fig.transFigure,arrowstyle="-|>",mutation_scale=28,color=INK2,lw=2.2))
fig.text(4.55/W,3.05/H,"case-study\ndistrict",fontsize=10,color=INK2,ha="center",va="center",style="italic")
# panel 2
fig.text(5.0/W,(H-0.95)/H,"2  District: which buildings?",fontsize=14,fontweight="bold",color=S2,va="center")
a2=ax_at(4.95,0.75,3.9,3.55); b.plot(ax=a2,column=b.form_factor.clip(1.0,2.5),cmap=ORNG,linewidth=0); a2.set_aspect("equal")
fig.text(5.0/W,0.42/H,"Open-data LOD1 BIM: 2,711 buildings, IFC\nINSPIRE parcels + OS outlines + EA LiDAR",fontsize=11.5,color=INK2,va="center",linespacing=1.35)
fig.text(8.75/W,1.1/H,"colour: form\nfactor (heat-loss\narea ÷ floor area)",fontsize=9,color=INK2,ha="right",va="center",linespacing=1.2)
# panel 3
x0=9.15; fig.text((x0+0.1)/W,(H-0.95)/H,"3  What decides within the district?",fontsize=14,fontweight="bold",color=INK,va="center")
a3=ax_at(x0+0.15,1.55,3.75,2.65); a3.set_axis_on()
vals=[("Predicted energy\n(open data)",V["Level1"]["total_T1"]["rho"],"#9aa3ad"),("EPC rating",V["RQ3"]["rho_EPCprimary_metered_intensity"],"#9aa3ad"),("BIM form factor",V["RQ3"]["rho_formfactor_metered_intensity"],S2)]
for i,(lab,v,col) in enumerate(vals):
    a3.barh(2-i,v,color=col,height=0.58); a3.text(v+0.015,2-i,f"{v:.2f}",va="center",fontsize=12,fontweight="bold",color=INK)
    a3.text(-0.02,2-i,lab,ha="right",va="center",fontsize=11,color=INK)
a3.set_xlim(0,0.55); a3.set_ylim(-0.6,2.6); a3.set_yticks([]); a3.set_xticks([0,0.25,0.5]); a3.tick_params(labelsize=9,colors=INK2)
for s in ["top","right","left"]: a3.spines[s].set_visible(False)
a3.set_xlabel("Spearman ρ vs metered energy\n(81 postcodes)",fontsize=9.5,color=INK2)
a3.set_position([(x0+1.55)/W,1.75/H,2.25/W,2.4/H])
box=FancyBboxPatch(((x0+0.1)/W,0.18/H),3.8/W,0.95/H,boxstyle="round,pad=0.005,rounding_size=0.01",transform=fig.transFigure,facecolor="#eef6ea",edgecolor=GREEN,lw=1.4); fig.patches.append(box)
fig.text((x0+2.0)/W,0.655/H,"Open data choose the neighbourhood;\nbuilding geometry chooses the buildings.",fontsize=12.5,fontweight="bold",color=GREEN,ha="center",va="center",linespacing=1.3)
for ext in ["png","pdf"]: fig.savefig(OUT+"Graphical_abstract."+ext,dpi=300)
from PIL import Image; im=Image.open(OUT+"Graphical_abstract.png"); print(im.size)
