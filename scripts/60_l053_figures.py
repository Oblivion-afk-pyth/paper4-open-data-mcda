"""Leeds 053 figures (300 dpi PNG + PDF). Palette: validated default categorical slots 1-2; sequential blue ramp."""
import os,json,numpy as np,pandas as pd,geopandas as gpd,matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import spearmanr
D=(__import__("paths").ROOT+""); O=D+"02_processed/v4_district/"; OUT=D+"03_outputs/v4_district/"; F=OUT+"figures/"
S1,S2="#2a78d6","#eb6834"; INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"; MUTED="#8f8e88"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK2,"ytick.color":INK2,
  "axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.axisbelow":True,"legend.frameon":False})
BLUE=LinearSegmentedColormap.from_list("b",["#e8f1fc","#9cc3f0","#2a78d6","#173f73"])
def save(fig,n): fig.savefig(F+n+".png",dpi=300,bbox_inches="tight"); fig.savefig(F+n+".pdf",bbox_inches="tight"); plt.close(fig)
T=pd.read_csv(O+"l053_postcode_table.csv",index_col=0); T=T[T.keep]
V=json.load(open(OUT+"l053_validation.json")); N=json.load(open(OUT+"l053_noise_mc_spatial.json"))
R=pd.read_csv(OUT+"l053_decision_validation.csv")
# ---------- Fig 1: prediction vs metered, citywide vs district
G=pd.read_csv(OUT+"leeds_outside_postcodes_pred_vs_met.csv",index_col=0)
fig,ax=plt.subplots(1,2,figsize=(7.6,3.4),sharex=True,sharey=True)
lim=(4000,32000)
hb=ax[0].hexbin(G.tot/1e3,G.met/1e3,gridsize=45,extent=(4,32,4,32),cmap=BLUE,mincnt=1,bins="log",linewidths=0)
ax[1].scatter(T.proxy_total_mean/1e3,T.met_total_mean/1e3,s=22,color=S1,edgecolor="white",linewidth=0.8,zorder=3)
for a,t,r,n in [(ax[0],"Leeds postcodes outside the district",spearmanr(G.tot,G.met).correlation,len(G)),(ax[1],"Leeds 053 (Harehills)",spearmanr(T.proxy_total_mean,T.met_total_mean).correlation,len(T))]:
    a.plot([4,32],[4,32],color=MUTED,lw=1,ls="--",zorder=2); a.set_xlim(4,32); a.set_ylim(4,32); a.set_aspect("equal")
    a.set_title(t,fontsize=9,color=INK,loc="left"); a.text(0.04,0.95,f"n = {n:,}\nSpearman ρ = {r:.2f}",transform=a.transAxes,va="top",color=INK2,fontsize=8)
    a.set_xlabel("Predicted mean energy, T1 (MWh/yr)")
ax[0].set_ylabel("Metered mean energy 2024 (MWh/yr)")
sd_out=np.log(G.met).std(); sd_in=np.log(T.met_total_mean).std()
ax[1].text(0.97,0.97,f"SD log(metered): {sd_in:.2f} (district)\nvs {sd_out:.2f} (rest of Leeds)\nSD log-residual: {np.log(T.met_total_mean/T.proxy_total_mean).std():.2f} vs {G.res_tot.std():.2f}",transform=ax[1].transAxes,ha="right",va="top",fontsize=7.5,color=INK2)
cb=fig.colorbar(hb,ax=list(ax),shrink=0.75,pad=0.02,location="right"); cb.set_label("Postcodes per cell",color=INK2,fontsize=8); cb.outline.set_visible(False)
save(fig,"Fig1_prediction_city_vs_district")
# ---------- Fig 2: decision agreement vs energy weight, six vs eight criteria, with bootstrap CIs and noise ceiling
boot={(b["case"],b["weights"]):b for b in V["bootstrap"]}
W=["objective","equal","e70","e90"]; lab=["Objective","Equal","70%\nenergy","90%\nenergy"]
fig,ax=plt.subplots(1,2,figsize=(7.2,3.2)); fig.subplots_adjust(wspace=0.35)
for j,(metric,ci,yl) in enumerate([("rho","rho_CI","Spearman ρ, proxy vs meter-informed"),("top20","top20_CI","Top-20% overlap (%)")]):
    a=ax[j]; x=np.arange(4)
    for k,(case,col,name,off) in enumerate([("T1c six criteria",S1,"Six criteria (EPC + area data)",-0.1),("T1c eight criteria",S2,"Eight criteria (+ BIM: C7, C8)",0.1)]):
        y=[R[(R.case==case)&(R.weights==w)&(R.method=="gra")][metric].iat[0] for w in W]
        c=[boot[("T1c "+case.split()[1],w)][ci] for w in W]
        a.errorbar(x+off,y,yerr=[[yy-cc[0] for yy,cc in zip(y,c)],[cc[1]-yy for yy,cc in zip(y,c)]],fmt="o",ms=6,color=col,ecolor=col,elinewidth=1.4,capsize=0,mec="white",mew=1,label=name,zorder=3)
    if metric=="rho":
        a.axhline(N["noise"]["max_attainable_r"],color=MUTED,ls="--",lw=1); a.text(3.45,N["noise"]["max_attainable_r"]+0.02,"noise ceiling",ha="right",va="bottom",fontsize=7.5,color=INK2)
        e=R[(R.case.str.contains("energy criteria only"))&(R.weights=="objective")].rho.iat[0]
        a.axhline(e,color=MUTED,ls=":",lw=1); a.text(1.5,e+0.02,"energy criteria only",ha="center",va="bottom",fontsize=7.5,color=INK2); a.set_ylim(0,1)
    else: a.set_ylim(0,105); a.axhline(20,color=MUTED,ls=":",lw=1); a.text(1.5,22,"chance (20%)",ha="center",fontsize=7.5,color=INK2)
    a.set_xticks(x); a.set_xticklabels(lab,fontsize=8); a.set_ylabel(yl); a.set_xlim(-0.5,3.5); a.grid(axis="x",visible=False)
ax[0].legend(loc="lower left",fontsize=7.5,bbox_to_anchor=(0,0.02))
ax[0].set_xlabel("Weighting scheme"); ax[1].set_xlabel("Weighting scheme")
save(fig,"Fig2_decision_agreement")
# ---------- Fig 3: BIM geometry – exposed perimeter by EPC built form; form factor vs metered intensity
b=gpd.read_file(O+"l053_buildings_v2.gpkg"); b1=b[b.lidar_ok&(b.n_epc==1)&b.built_form.notna()]
order=["Enclosed Mid-Terrace","Mid-Terrace","Enclosed End-Terrace","End-Terrace","Semi-Detached"]; nm=["Back-to-\nback","Mid-\nterrace","Encl. end-\nterrace","End-\nterrace","Semi-\ndetached"]
fig,ax=plt.subplots(1,2,figsize=(7.6,3.3),gridspec_kw={"width_ratios":[1.25,1]}); fig.subplots_adjust(wspace=0.3)
data=[b1[b1.built_form==o].exposed_perim_m.clip(upper=40).values for o in order]
bp=ax[0].boxplot(data,widths=0.55,patch_artist=True,showfliers=False,medianprops=dict(color=INK,lw=1.4),whiskerprops=dict(color=MUTED),capprops=dict(color=MUTED),boxprops=dict(edgecolor=S1,lw=1))
for p in bp["boxes"]: p.set_facecolor("#d3e4f8")
ax[0].set_xticks(range(1,6)); ax[0].set_xticklabels([f"{n}\n(n={len(d)})" for n,d in zip(nm,data)],fontsize=7)
ax[0].set_ylabel("Exposed perimeter from LiDAR BIM (m)"); ax[0].grid(axis="x",visible=False)
ax[0].set_title("a  Geometry vs EPC built form",loc="left",fontsize=9)
mi=T.met_total_mean/T.mean_tfa
ax[1].scatter(T.C7_form_factor,mi,s=22,color=S1,edgecolor="white",lw=0.8,zorder=3)
z=np.polyfit(T.C7_form_factor,mi,1); xx=np.linspace(T.C7_form_factor.min(),T.C7_form_factor.max(),10); ax[1].plot(xx,np.polyval(z,xx),color=S2,lw=2)
ax[1].set_xlabel("Form factor, postcode median (C7)"); ax[1].set_ylabel("Metered intensity (kWh/m²·yr)")
ax[1].text(0.97,0.05,f"ρ = {V['RQ3']['rho_formfactor_metered_intensity']:.2f}\npartial on EPC rating = {V['RQ3']['partial_rho_formfactor_intensity|EPC_primary']:.2f}\nEPC rating alone ρ = {V['RQ3']['rho_EPCprimary_metered_intensity']:.2f}",transform=ax[1].transAxes,ha="right",va="bottom",fontsize=7.5,color=INK2)
ax[1].set_title("b  Form factor vs metered intensity",loc="left",fontsize=9)
save(fig,"Fig3_bim_geometry")
# ---------- Fig 4: maps – postcode P(top 20%) and building-level top 20%
pt=pd.read_csv(OUT+"l053_montecarlo_ptop20.csv",index_col=0)["objective"]
sc=pd.read_csv(OUT+"l053_building_scores.csv",index_col=0)
h=pd.read_csv(O+"l053_epc_linked.csv",low_memory=False); bpc=h[h.bid.notna()].groupby("bid").postcode.agg(lambda s:s.mode().iat[0])
b["postcode"]=b.bid.map(bpc); b["ptop"]=b.postcode.map(pt); b["top_b"]=b.bid.map(sc.top20_building)
fig,ax=plt.subplots(1,2,figsize=(7.2,4.2))
for a in ax: b.plot(ax=a,color="#e4e3df",linewidth=0); a.set_axis_off(); a.set_aspect("equal")
m=b[b.ptop.notna()]; m.plot(ax=ax[0],column="ptop",cmap=BLUE,vmin=0,vmax=1,linewidth=0)
sm=plt.cm.ScalarMappable(cmap=BLUE,norm=plt.Normalize(0,1)); cb=fig.colorbar(sm,ax=ax[0],shrink=0.6,orientation="horizontal",pad=0.02); cb.set_label("P(postcode in top 20%), Monte Carlo",fontsize=8,color=INK2); cb.outline.set_visible(False)
ax[0].set_title("a  Postcode priority (81 postcodes)",loc="left",fontsize=9)
b[b.top_b==False].plot(ax=ax[1],color="#9cc3f0",linewidth=0); b[b.top_b==True].plot(ax=ax[1],color=S2,linewidth=0)
from matplotlib.patches import Patch
ax[1].legend(handles=[Patch(color=S2,label="Top 20% buildings"),Patch(color="#9cc3f0",label="Other scored buildings"),Patch(color="#e4e3df",label="Not scored")],loc="lower left",fontsize=7.5,bbox_to_anchor=(0,-0.12))
ax[1].set_title(f"b  Building priority (illustrative, n={len(sc):,})",loc="left",fontsize=9)
x0,y0=b.total_bounds[:2]; ax[0].plot([x0+20,x0+220],[y0-20,y0-20],color=INK,lw=2); ax[0].text(x0+120,y0-45,"200 m",ha="center",va="top",fontsize=7.5)
save(fig,"Fig4_priority_maps")
print(sorted(os.listdir(F)))
