"""v2 figures."""
import pandas as pd, numpy as np, geopandas as gpd, matplotlib, json, sys
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
sys.path.insert(0,"scripts"); from mcda import gra, combined_w, entropy_w, critic_w; from mcda_v2 import *
BLUE,ORANGE,AQUA,INK,MUTED,GRID="#2a78d6","#eb6834","#1baf7a","#1f1f1e","#8a897f","#e4e3dc"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK,"ytick.color":INK,"axes.titlesize":9.5})
F="03_outputs/v2/figures/"; O="03_outputs/v2/"
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); C=A[A.la=="E08000035"]
g=gpd.read_file("02_processed/leeds_lsoa_2021.gpkg").set_index("lsoa21cd")
M=pd.read_csv(O+"matrix_leeds_T0.csv",index_col=0); Pc=pd.read_csv(O+"matrix_leeds_T1c.csv",index_col=0); P1=pd.read_csv(O+"matrix_leeds_T1.csv",index_col=0)
def clean(ax): ax.spines[["top","right"]].set_visible(False); ax.grid(color=GRID,lw=0.6,zorder=0)
lab={"C1_energy_intensity":"C1 Energy intensity","C2_carbon_abatement":"C2 Carbon abatement","C3_fuel_poverty":"C3 Fuel poverty","C4_income_deprivation":"C4 Income deprivation","C5_cost_effectiveness":"C5 Cost-effectiveness","C6_stock_homogeneity":"C6 Stock homogeneity"}
units={"C1_energy_intensity":"kWh m⁻² yr⁻¹","C2_carbon_abatement":"t CO₂e dwelling⁻¹ yr⁻¹","C3_fuel_poverty":"% households","C4_income_deprivation":"IoD 2025 income rate","C5_cost_effectiveness":"kWh yr⁻¹ per £ (2024)","C6_stock_homogeneity":"% in dominant archetype"}
# Fig 2 Level 1 scatter
o=C.met_total_mean/1000; lo,hi=4,32
fig,axs=plt.subplots(1,3,figsize=(7.4,2.8),sharey=True)
for ax,(t,p,col),k in zip(axs,[("EPC-derived baseline (approx.)",C.epc_total_mean,MUTED),("Proxy T1",C.proxy_total_mean,BLUE),("Proxy T1c",C.proxyc_total_mean,ORANGE)],"abc"):
    p=p/1000; mape=100*(abs(p-o)/o).mean(); r2=1-((o-p)**2).sum()/((o-o.mean())**2).sum()
    ax.plot([lo,hi],[lo,hi],color=MUTED,lw=1,ls=(0,(4,3)),zorder=1); ax.scatter(o,p,s=10,color=col,alpha=0.75,edgecolor="white",linewidth=0.3,zorder=3)
    ax.set_xlim(lo,hi); ax.set_ylim(lo,hi); ax.set_aspect("equal"); clean(ax); ax.set_title(f"({k}) {t}",loc="left",fontsize=8.8); ax.set_xlabel("Metered (MWh dwelling⁻¹ yr⁻¹)")
    ax.text(0.04,0.96,f"MAPE {mape:.1f}%\nR² {r2:.2f}",transform=ax.transAxes,va="top",fontsize=8)
axs[0].set_ylabel("Estimated (MWh dwelling⁻¹ yr⁻¹)"); plt.tight_layout(); plt.savefig(F+"fig2_level1_scatter.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 3 criteria maps
G=g.join(M); fig,axs=plt.subplots(2,3,figsize=(7.4,4.6))
for ax,c,k in zip(axs.flat,M.columns,"abcdef"):
    G.plot(column=c,cmap="Blues",ax=ax,legend=True,legend_kwds={"shrink":0.62,"label":units[c]},linewidth=0.05,edgecolor="white",vmin=G[c].quantile(0.02),vmax=G[c].quantile(0.98))
    ax.set_title(f"({k}) {lab[c]}",loc="left"); ax.set_axis_off()
plt.tight_layout(); plt.savefig(F+"fig3_criteria_maps.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 4 correlation heatmap
Cr=M.corr(method="spearman"); fig,ax=plt.subplots(figsize=(4.8,4.0)); im=ax.imshow(Cr.values,cmap="RdBu_r",vmin=-1,vmax=1)
ax.set_xticks(range(6)); ax.set_yticks(range(6)); nm=[lab[c].split(" ")[0] for c in Cr.columns]; ax.set_xticklabels(nm); ax.set_yticklabels([lab[c] for c in Cr.columns])
for i in range(6):
    for j in range(6): ax.text(j,i,f"{Cr.values[i,j]:.2f}",ha="center",va="center",fontsize=7.5,color="white" if abs(Cr.values[i,j])>0.6 else INK)
fig.colorbar(im,ax=ax,shrink=0.8,label="Spearman correlation"); plt.tight_layout(); plt.savefig(F+"fig4_criteria_correlation.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 5 weights (proxy T1c)
W=pd.DataFrame({"Entropy":entropy_w(Pc),"CRITIC":critic_w(Pc),"Combined (entropy × CRITIC)":combined_w(Pc)})
fig,ax=plt.subplots(figsize=(6.2,3.2)); y=np.arange(6); bh=0.26
for i,(c,col) in enumerate(zip(W.columns,[MUTED,BLUE,ORANGE])): ax.barh(y+(i-1)*bh,W[c].values,height=bh-0.03,color=col,label=c,zorder=3)
for yy,v in zip(y,W.iloc[:,2].values): ax.text(v+0.008,yy+bh,f"{v:.2f}",va="center",fontsize=7.5)
ax.set_yticks(y); ax.set_yticklabels([lab[c] for c in W.index]); ax.invert_yaxis(); ax.set_xlabel("Weight"); clean(ax); ax.grid(axis="y",visible=False); ax.legend(frameon=False,loc="lower right",fontsize=7.5)
plt.tight_layout(); plt.savefig(F+"fig5_weights.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 6 agreement vs energy share with CIs
D=pd.read_csv(O+"decision_validation_v2.csv"); b=json.load(open(O+"bootstrap_ci_v2.json"))
wmap={"objective":0.28,"equal":0.5,"e70":0.7,"e90":0.9}
fig,axs=plt.subplots(1,2,figsize=(7.2,3.1))
for ax,met,thr,yl in [(axs[0],"rho",0.8,"Spearman ρ"),(axs[1],"top20",70,"Top-20% overlap (%)")]:
    ax.axhline(thr,color=MUTED,lw=1,ls=(0,(4,3)))
    for city,mk in [("leeds","o"),("bradford","s")]:
        for tier,col in [("T1",BLUE),("T1c",ORANGE)]:
            d=D[(D.city==city)&(D.case==f"{tier} six criteria")&(D.method=="gra")&(~D.own_weights)].copy(); d["x"]=d.weights.map(wmap); d=d.sort_values("x")
            ax.plot(d.x,d[met],marker=mk,color=col,ls="-" if city=="leeds" else ":",ms=6,mec="white",label=f"{tier}, {city.capitalize()}")
    for r in b:
        x=wmap[r["weights"]]; lohi=r["rho_CI"] if met=="rho" else r["top20_CI"]; ax.plot([x,x],lohi,color=ORANGE,lw=2,alpha=0.45)
    ax.set_xticks([0.28,0.5,0.7,0.9]); ax.set_xticklabels(["28%\n(objective)","50%\n(equal)","70%","90%"]); ax.set_xlabel("Weight on energy criteria"); ax.set_ylabel(yl); clean(ax)
axs[0].set_title("(a) Rank correlation",loc="left"); axs[1].set_title("(b) Top-priority overlap",loc="left"); axs[0].legend(frameon=False,fontsize=7,loc="lower left")
plt.tight_layout(); plt.savefig(F+"fig6_agreement_vs_energy_weight.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 7 rank-rank
n=len(M); k=int(round(0.2*n)); fig,axs=plt.subplots(1,2,figsize=(6.6,3.3),sharey=True)
for ax,(t,w),kk in zip(axs,[("Objective weights",combined_w(Pc)),("Equal weights",pd.Series(1/6,index=M.columns))],"ab"):
    rM=rank(gra(M,w)); rP=rank(gra(Pc,w)); both=(rM<=k)&(rP<=k); one=((rM<=k)^(rP<=k))
    ax.axvspan(0,k,color="#f3f2ec",zorder=0); ax.axhspan(0,k,color="#f3f2ec",zorder=0); ax.plot([0,n],[0,n],color=MUTED,lw=1,ls=(0,(4,3)))
    ax.scatter(rM[~both&~one],rP[~both&~one],s=6,color=MUTED,alpha=0.6,label="Neither top 20%"); ax.scatter(rM[one],rP[one],s=10,color=ORANGE,label="Top 20% in one ranking only"); ax.scatter(rM[both],rP[both],s=10,color=BLUE,label="Top 20% in both")
    a=agree(gra(Pc,w),gra(M,w)); ax.text(0.97,0.04,f"ρ = {a['rho']:.2f}\noverlap {a['top20']:.0f}%",transform=ax.transAxes,ha="right",fontsize=8)
    ax.set_xlim(0,n+5); ax.set_ylim(0,n+5); ax.set_aspect("equal"); ax.set_title(f"({kk}) {t}",loc="left"); ax.set_xlabel("Reference rank (T0)"); ax.spines[["top","right"]].set_visible(False)
axs[0].set_ylabel("Proxy rank (T1c)"); axs[0].legend(frameon=False,loc="upper left",fontsize=7); plt.tight_layout(); plt.savefig(F+"fig7_rank_agreement.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 8 rank shift maps
S=pd.read_csv(O+"rq4_residuals_shifts.csv",index_col=0); sp=json.load(open(O+"spatial_v2.json"))
eq=pd.Series(1/6,index=M.columns); GG=g.join(S); GG["rank_T0"]=rank(gra(M,eq))
fig=plt.figure(figsize=(7.2,7.4)); gs=fig.add_gridspec(2,2,height_ratios=[1.15,1],hspace=0.12,wspace=0.05)
a=fig.add_subplot(gs[0,:]); b_=fig.add_subplot(gs[1,0]); c_=fig.add_subplot(gs[1,1])
GG.plot(column="rank_T0",cmap="viridis_r",ax=a,legend=True,legend_kwds={"shrink":0.7,"label":"Reference priority rank (1 = most urgent)"},linewidth=0.05,edgecolor="white"); a.set_title("(a) Meter-informed reference ranking (T0), equal weights",loc="left",fontsize=10)
lim=max(abs(GG.shift_T1).max(),abs(GG.shift_T1c).max()); norm=TwoSlopeNorm(0,-lim,lim)
for ax,col,t in [(b_,"shift_T1",f"(b) Rank shift, T1 (Moran's I = {sp['shift_T1']['I']:.2f})"),(c_,"shift_T1c",f"(c) Rank shift, T1c (Moran's I = {sp['shift_T1c']['I']:.2f})")]:
    GG.plot(column=col,cmap="RdBu",norm=norm,ax=ax,linewidth=0.05,edgecolor="white"); ax.set_title(t,loc="left",fontsize=9)
for ax in (a,b_,c_): ax.set_axis_off()
cb=fig.colorbar(plt.cm.ScalarMappable(cmap="RdBu",norm=norm),ax=[b_,c_],orientation="horizontal",fraction=0.05,pad=0.02,aspect=40); cb.set_label("Proxy rank − reference rank   (red: proxy more urgent; blue: less urgent)")
plt.savefig(F+"fig8_rank_shift_maps.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 9 tiers
T=pd.read_csv(O+"tiers_v2.csv"); order=["T1c","T1","T2","T3","T4"]; labx=["T1c\nfull +\ncorrection","T1\nfull open\ndata","T2\nproperty\nregister","T3\nhousing\ntypology","T4\ndeprivation\nonly"]
fig,axs=plt.subplots(1,2,figsize=(7.4,3.3))
for ax,met,thr,yl in [(axs[0],"rho",0.8,"Spearman ρ vs reference"),(axs[1],"top20",70,"Top-20% overlap (%)")]:
    ax.axhline(thr,color=MUTED,lw=1,ls=(0,(4,3)))
    for w,col,nm in [("objective",BLUE,"Objective weights"),("equal",ORANGE,"Equal weights"),("e70",AQUA,"70% energy")]:
        d=T[(T.reference=="6-criterion reference")&(T.weights==w)].set_index("tier").loc[order]; ax.plot(range(5),d[met],marker="o",color=col,ms=7,mec="white",label=nm)
        d5=T[(T.reference!="6-criterion reference")&(T.weights==w)]; ax.scatter([4],d5[met],marker="D",facecolor="white",edgecolor=col,s=28,zorder=4)
    ax.set_xticks(range(5)); ax.set_xticklabels(labx,fontsize=7.5); ax.set_ylabel(yl); clean(ax)
axs[0].set_title("(a) Rank correlation",loc="left"); axs[1].set_title("(b) Top-priority overlap",loc="left"); axs[0].legend(frameon=False,fontsize=7,loc="lower left")
fig.text(0.01,-0.03,"Open diamonds at T4: comparison with a five-criterion reference without C6.",fontsize=7.5,color=MUTED)
plt.tight_layout(); plt.savefig(F+"fig9_data_reduction.png",dpi=300,bbox_inches="tight"); plt.close()
# Fig 10 MC maps (spatially correlated model)
p=pd.read_csv(O+"montecarlo_ptop20_v2.csv",index_col=0); fig,axs=plt.subplots(1,2,figsize=(7.2,3.3))
for ax,(w,t),kk in zip(axs,[("objective","Objective weights"),("equal","Equal weights")],"ab"):
    wf=combined_w(M) if w=="objective" else pd.Series(1/6,index=M.columns); rM=rank(gra(M,wf))
    g.join(p[f"{w}|C_empirical_spatial"].rename("p")).plot(column="p",cmap="Blues",vmin=0,vmax=1,ax=ax,linewidth=0.05,edgecolor="white")
    g[g.index.isin(rM[rM<=k].index)].boundary.plot(ax=ax,color=ORANGE,linewidth=0.6); ax.set_title(f"({kk}) {t}",loc="left"); ax.set_axis_off()
cb=fig.colorbar(plt.cm.ScalarMappable(cmap="Blues",norm=plt.Normalize(0,1)),ax=axs,orientation="horizontal",fraction=0.05,pad=0.03,aspect=40); cb.set_label("Probability of ranking in the proxy top 20% (orange outline: reference top 20%)")
plt.savefig(F+"fig10_montecarlo_maps.png",dpi=300,bbox_inches="tight"); plt.close(); print("done")
