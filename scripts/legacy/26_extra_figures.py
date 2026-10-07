"""Additional manuscript figures (4-8)."""
import pandas as pd, numpy as np, geopandas as gpd, matplotlib, sys
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr
sys.path.insert(0,"scripts"); from mcda import *
BLUE,ORANGE,AQUA,INK,MUTED,GRID="#2a78d6","#eb6834","#1baf7a","#1f1f1e","#8a897f","#e4e3dc"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK,"ytick.color":INK,"axes.titlesize":9.5})
F="03_outputs/figures/"
g=gpd.read_file("02_processed/leeds_lsoa_2021.gpkg").set_index("lsoa21cd")
M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0); Pc=pd.read_csv("03_outputs/matrix_proxy_T1c.csv",index_col=0); P1=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0)
def clean(ax): ax.spines[["top","right"]].set_visible(False); ax.grid(color=GRID,lw=0.6,zorder=0)
# ---- Fig 4: criteria maps (metered benchmark)
lab={"C1_energy_intensity":("C1 Energy intensity","kWh m⁻² yr⁻¹"),"C2_carbon_abatement":("C2 Carbon abatement","t CO₂e dwelling⁻¹ yr⁻¹"),
     "C3_fuel_poverty":("C3 Fuel poverty","% households"),"C4_income_deprivation":("C4 Income deprivation","IoD 2025 income rate"),
     "C5_cost_effectiveness":("C5 Cost-effectiveness","kWh yr⁻¹ per £"),"C6_delivery_eff":("C6 Delivery efficiency","% in dominant archetype")}
G=g.join(M); fig,axs=plt.subplots(2,3,figsize=(7.4,4.6))
for ax,(c,(t,u)),k in zip(axs.flat,lab.items(),"abcdef"):
    G.plot(column=c,cmap="Blues",ax=ax,legend=True,legend_kwds={"shrink":0.62,"label":u},linewidth=0.05,edgecolor="white",
           vmin=G[c].quantile(0.02),vmax=G[c].quantile(0.98))
    ax.set_title(f"({k}) {t}",loc="left"); ax.set_axis_off()
plt.tight_layout(); plt.savefig(F+"fig4_criteria_maps.png",dpi=300,bbox_inches="tight"); plt.close()
# ---- Fig 5: Level 1 scatter
L=pd.read_csv("03_outputs/level1_lsoa_estimates_vs_metered.csv",index_col=0); Tc=pd.read_csv("02_processed/leeds_lsoa_T1c.csv",index_col=0)
series=[("Raw EPC",L.epc_total_mean,MUTED),("Proxy T1",L.proxy_total_mean,BLUE),("Proxy T1c",Tc.proxyc_total_mean.reindex(L.index),ORANGE)]
o=L.met_total_mean/1000; lo,hi=4,31
fig,axs=plt.subplots(1,3,figsize=(7.4,2.8),sharey=True)
for ax,(t,p,col),k in zip(axs,series,"abc"):
    p=p/1000; mape=100*(abs(p-o)/o).mean(); r2=1-((o-p)**2).sum()/((o-o.mean())**2).sum()
    ax.plot([lo,hi],[lo,hi],color=MUTED,lw=1,ls=(0,(4,3)),zorder=1)
    ax.scatter(o,p,s=10,color=col,alpha=0.75,edgecolor="white",linewidth=0.3,zorder=3)
    ax.set_xlim(lo,hi); ax.set_ylim(lo,hi); ax.set_aspect("equal"); clean(ax)
    ax.set_title(f"({k}) {t}",loc="left"); ax.set_xlabel("Metered (MWh dwelling⁻¹ yr⁻¹)")
    ax.text(0.04,0.96,f"MAPE {mape:.1f}%\nR² {r2:.2f}",transform=ax.transAxes,va="top",fontsize=8,color=INK)
axs[0].set_ylabel("Estimated (MWh dwelling⁻¹ yr⁻¹)")
plt.tight_layout(); plt.savefig(F+"fig5_level1_scatter.png",dpi=300,bbox_inches="tight"); plt.close()
# ---- Fig 6: weights
W=pd.read_csv("03_outputs/weights.csv",index_col=0)
names=["C1 Energy intensity","C2 Carbon abatement","C3 Fuel poverty","C4 Income deprivation","C5 Cost-effectiveness","C6 Delivery efficiency"]
fig,ax=plt.subplots(figsize=(6.2,3.2)); y=np.arange(6); bh=0.26
for i,(c,col,nm) in enumerate([("entropy_P",MUTED,"Entropy"),("critic_P",BLUE,"CRITIC"),("combined_P",ORANGE,"Combined (entropy × CRITIC)")]):
    ax.barh(y+(1-i)*bh,W[c].values,height=bh-0.03,color=col,label=nm,zorder=3)
for yy,v in zip(y,W.combined_P.values): ax.text(v+0.008,yy-bh,f"{v:.2f}",va="center",fontsize=7.5,color=INK)
ax.set_yticks(y); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlabel("Weight"); clean(ax); ax.grid(axis="y",visible=False)
hh,ll=ax.get_legend_handles_labels(); ax.legend(hh[::-1],ll[::-1],frameon=False,loc="lower right",fontsize=7.5)
plt.tight_layout(); plt.savefig(F+"fig6_weights.png",dpi=300,bbox_inches="tight"); plt.close()
# ---- Fig 7: rank-rank scatter
fig,axs=plt.subplots(1,2,figsize=(6.6,3.3),sharey=True); n=len(M); k=int(round(0.2*n))
for ax,(t,wf),kk in zip(axs,[("Objective weights",combined_w),("Equal weights",lambda X:pd.Series(1/6,index=X.columns))],"ab"):
    rM=rank(gra(M,wf(M))); rP=rank(gra(Pc,wf(Pc)))
    both=(rM<=k)&(rP<=k); one=((rM<=k)^(rP<=k))
    ax.axvspan(0,k,color="#f3f2ec",zorder=0); ax.axhspan(0,k,color="#f3f2ec",zorder=0)
    ax.plot([0,n],[0,n],color=MUTED,lw=1,ls=(0,(4,3)),zorder=1)
    ax.scatter(rM[~both&~one],rP[~both&~one],s=6,color=MUTED,alpha=0.6,zorder=2,label="Neither top 20%")
    ax.scatter(rM[one],rP[one],s=10,color=ORANGE,zorder=3,label="Top 20% in one ranking only")
    ax.scatter(rM[both],rP[both],s=10,color=BLUE,zorder=4,label="Top 20% in both")
    rho=spearmanr(rM,rP).correlation; ax.text(0.97,0.04,f"ρ = {rho:.2f}\noverlap {100*both.sum()/k:.0f}%",transform=ax.transAxes,ha="right",fontsize=8)
    ax.set_xlim(0,n+5); ax.set_ylim(0,n+5); ax.set_aspect("equal"); ax.set_title(f"({kk}) {t}",loc="left"); ax.set_xlabel("Metered rank (T0)")
    ax.spines[["top","right"]].set_visible(False)
axs[0].set_ylabel("Proxy rank (T1c)"); axs[0].legend(frameon=False,loc="upper left",fontsize=7,markerscale=1.5)
plt.tight_layout(); plt.savefig(F+"fig7_rank_agreement.png",dpi=300,bbox_inches="tight"); plt.close()
# ---- Fig 8: Monte Carlo top-20 probability maps
fig,axs=plt.subplots(1,2,figsize=(7.2,3.3))
for ax,(wn,t),kk in zip(axs,[("objective","Objective weights"),("equal","Equal weights")],"ab"):
    p=pd.read_csv(f"03_outputs/montecarlo_p_top20_{wn}.csv",index_col=0).iloc[:,0]
    wf=combined_w if wn=="objective" else (lambda X:pd.Series(1/6,index=X.columns)); rM=rank(gra(M,wf(M)))
    GG=g.join(p.rename("p")); GG.plot(column="p",cmap="Blues",vmin=0,vmax=1,ax=ax,linewidth=0.05,edgecolor="white")
    g[g.index.isin(rM[rM<=k].index)].boundary.plot(ax=ax,color=ORANGE,linewidth=0.6)
    ax.set_title(f"({kk}) {t}",loc="left"); ax.set_axis_off()
sm=plt.cm.ScalarMappable(cmap="Blues",norm=plt.Normalize(0,1)); cb=fig.colorbar(sm,ax=axs,orientation="horizontal",fraction=0.05,pad=0.03,aspect=40)
cb.set_label("Probability of ranking in the proxy top 20% (orange outline: metered top 20%)")
plt.savefig(F+"fig8_montecarlo_maps.png",dpi=300,bbox_inches="tight"); plt.close()
print("done")
