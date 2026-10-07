"""Fix: predicted vs metered postcode figure (manuscript Fig. 6). Colourbar on hexbin panel only; no text overlap; y labels on both panels."""
import os,numpy as np,pandas as pd,matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr
D=(__import__("paths").ROOT+""); O=D+"02_processed/v4_district/"; OUT=D+"03_outputs/v4_district/"; F=OUT+"figures/"
S1,S2="#2a78d6","#eb6834"; INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; MUTED="#8f8e88"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK2,"ytick.color":INK2,
  "axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.axisbelow":True})
BLUE=LinearSegmentedColormap.from_list("b",["#e8f1fc","#9cc3f0","#2a78d6","#173f73"])
T=pd.read_csv(O+"l053_postcode_table.csv",index_col=0); T=T[T.keep]
G=pd.read_csv(OUT+"leeds_outside_postcodes_pred_vs_met.csv",index_col=0)
fig=plt.figure(figsize=(8.4,3.9))
gs=fig.add_gridspec(1,4,width_ratios=[1,0.045,0.32,1],wspace=0.05)
a0=fig.add_subplot(gs[0]); cax=fig.add_subplot(gs[1]); a1=fig.add_subplot(gs[3])
hb=a0.hexbin(G.tot/1e3,G.met/1e3,gridsize=45,extent=(4,32,4,32),cmap=BLUE,mincnt=1,bins="log",linewidths=0)
a1.scatter(T.proxy_total_mean/1e3,T.met_total_mean/1e3,s=24,color=S1,edgecolor="white",linewidth=0.8,zorder=3)
rows=[(a0,"a  Leeds postcodes outside the district",spearmanr(G.tot,G.met).correlation,len(G)),
      (a1,"b  Leeds 053 (Harehills)",spearmanr(T.proxy_total_mean,T.met_total_mean).correlation,len(T))]
for a,t,r,n in rows:
    a.plot([4,32],[4,32],color=MUTED,lw=1,ls="--",zorder=2); a.set_xlim(4,32); a.set_ylim(4,32); a.set_aspect("equal")
    a.set_xticks([5,10,15,20,25,30]); a.set_yticks([5,10,15,20,25,30])
    a.set_title(t,fontsize=9.5,color=INK,loc="left")
    a.text(0.04,0.96,f"n = {n:,}\nSpearman ρ = {r:.2f}",transform=a.transAxes,va="top",ha="left",color=INK,fontsize=8.5,
           bbox=dict(boxstyle="round,pad=0.3",fc="white",ec="none",alpha=0.9))
    a.set_xlabel("Predicted mean energy, T1 (MWh/yr)"); a.set_ylabel("Metered mean energy 2024 (MWh/yr)")
sd_out=np.log(G.met).std(); sd_in=np.log(T.met_total_mean).std()
res_in=np.log(T.met_total_mean/T.proxy_total_mean).std(); res_out=G.res_tot.std()
a1.text(0.97,0.04,f"SD of log metered\n district {sd_in:.2f} | rest {sd_out:.2f}\nSD of log residual\n district {res_in:.2f} | rest {res_out:.2f}",
        transform=a1.transAxes,ha="right",va="bottom",fontsize=7.6,color=INK2,linespacing=1.35,bbox=dict(boxstyle="round,pad=0.35",fc="white",ec=GRID))
cb=fig.colorbar(hb,cax=cax); cb.set_label("Postcodes per hexagon",color=INK2,fontsize=8); cb.outline.set_visible(False); cax.tick_params(labelsize=7.5)
for ext in ["png","pdf"]: fig.savefig(F+"Fig1_prediction_city_vs_district."+ext,dpi=300,bbox_inches="tight")
print("ok",round(sd_in,2),round(sd_out,2),round(res_in,2),round(res_out,2))
