"""Leeds 053: (1) reliability ceiling of postcode metered means (household noise from NEED within-cell variance);
(2) out-of-district postcode residuals (Leeds postcodes outside E02002382) and Monte Carlo of proxy error;
(3) Moran's I (kNN, k=6) of prediction residuals and rank shifts."""
import os,sys,json,numpy as np,pandas as pd
from scipy.stats import spearmanr
D=(__import__("paths").ROOT+""); P=D+"02_processed/"; O=P+"v4_district/"; OUT=D+"03_outputs/v4_district/"
sys.path.insert(0,D+"scripts"); from mcda import gra,combined_w; from mcda_v2 import matrix,agree,rank
T=pd.read_csv(O+"l053_postcode_table.csv",index_col=0); T=T[T.keep]; out={}
# ---- (1) household noise: pooled within-cell variance of household total (gas+elec 2024), Yorkshire & Humber, gas-heated
n=pd.read_parquet(P+"need2026_england_slim.parquet")
n=n[(n.REGION=="E12000003")&(n.MAIN_HEAT_FUEL==1)&(n.GasValFlag2024=="V")&(n.ElecValFlag2024=="V")].copy()
n["tot"]=n.Gcons2024+n.Econs2024
cell=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","IMD_BAND_ENG"]
h=pd.read_csv(O+"l053_epc_linked.csv",low_memory=False); h=h[h.postcode.isin(T.index)]
dc=h.groupby(cell).size().rename("w")
g=n.groupby(cell).tot.agg(["var","size"]).join(dc,how="inner"); g=g[g["size"]>=30]
s2=float((g["var"]*g.w).sum()/g.w.sum())
noise=s2/T.elec_meters; var_obs=float(T.met_total_mean.var())
rel=max(0.0,1-float(noise.mean())/var_obs)
out["noise"]=dict(NEED_households=len(n),cells_used=len(g),share_district_dwellings_in_cells=round(float(g.w.sum()/len(h)),3),
  sd_household_kWh=round(np.sqrt(s2)),mean_meters_per_postcode=round(float(T.elec_meters.mean()),1),
  sd_noise_postcode_mean_kWh=round(float(np.sqrt(noise.mean()))),sd_observed_postcode_means_kWh=round(np.sqrt(var_obs)),
  reliability=round(rel,3),max_attainable_R2=round(rel,3),max_attainable_r=round(np.sqrt(rel),3))
for v,c in [("T1","proxy_total_mean"),("T1c","proxyc_total_mean")]:
    r=spearmanr(T[c],T.met_total_mean).correlation; out["noise"][f"rho_{v}_observed"]=round(float(r),3); out["noise"][f"rho_{v}_disattenuated"]=round(float(r/np.sqrt(rel)),3) if rel>0 else None
# ---- (2) out-of-district postcode residuals (Leeds)
pr=pd.read_parquet(P+"v2/leeds_dwelling_predictions_v2.parquet",columns=["certificate_number","lsoa21cd","msoa21cd","pred_gas","pred_elec","lodgement_year"])
pr=pr[(pr.msoa21cd!="E02002382")&(pr.lodgement_year<=2024)]
import glob
pc=pd.concat((pd.read_csv(f,dtype=str,usecols=["certificate_number","postcode"]) for f in sorted(glob.glob(P+"epc_parts/certificates-*_leeds.csv")) if "(1)" not in f)).drop_duplicates("certificate_number"); pc["postcode"]=pc.postcode.str.upper().str.strip()
pr=pr.merge(pc,on="certificate_number"); A=pd.read_csv(P+"v2/lsoa_table_v2.csv",index_col=0)
pr["tot"]=pr.pred_gas+pr.pred_elec; pr["totc"]=pr.tot*pr.lsoa21cd.map(A.proxyc_total_mean/A.proxy_total_mean)
G=pr.groupby("postcode").agg(n_epc=("tot","size"),tot=("tot","mean"),totc=("totc","mean"))
gm=pd.read_csv(P+"leeds_postcode_gas_2024.csv").set_index("Postcode"); em=pd.read_csv(P+"leeds_postcode_elec_2024.csv").set_index("Postcode")
G=G.join(gm[["Num_meters","Mean_cons_kwh"]].add_prefix("g_")).join(em[["Num_meters","Mean_cons_kwh"]].add_prefix("e_")).dropna()
G["share"]=(G.g_Num_meters/G.e_Num_meters).clip(upper=1); G["met"]=G.g_Mean_cons_kwh*G.share+G.e_Mean_cons_kwh
G=G[(G.n_epc>=5)&(G.n_epc/G.e_Num_meters>=0.5)]
for v in ["tot","totc"]: G[f"res_{v}"]=np.log(G.met/G[v])
G.to_csv(OUT+"leeds_outside_postcodes_pred_vs_met.csv")
out["outside_postcodes"]=dict(n=len(G),rho_T1=round(float(spearmanr(G.tot,G.met).correlation),3),rho_T1c=round(float(spearmanr(G.totc,G.met).correlation),3),
  sd_logres_T1=round(float(G.res_tot.std()),3),sd_logres_T1c=round(float(G.res_totc.std()),3))
loc=np.log(T.met_total_mean/T.proxyc_total_mean); out["district_sd_logres_T1c"]=round(float(loc.std()),3)
# Monte Carlo: centred empirical residuals, applied jointly to C1, C2, C5 (T1c, eight criteria)
rng=np.random.default_rng(2026); E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]; BIM=["C7_form_factor","C8_pv_area_dw"]
Pm=matrix(T,"T1c").join(T[BIM]); Mm=matrix(T,"M").join(T[BIM]); e0=(G.res_totc-G.res_totc.mean()).values; k=int(round(0.2*len(T)))
mc={}; ptop={}
for w in ["objective","equal"]:
    wP=combined_w(Pm) if w=="objective" else pd.Series(1/Pm.shape[1],index=Pm.columns)
    sM=gra(Mm,wP); topM=set(rank(sM)[rank(sM)<=k].index); sP0=gra(Pm,wP); topP0=set(rank(sP0)[rank(sP0)<=k].index)
    cnt=pd.Series(0,index=Pm.index); rh=[]; ov=[]; ovP=[]
    for _ in range(1000):
        X=Pm.copy(); f=np.exp(rng.choice(e0,len(X))); X[E]=X[E].mul(f,axis=0)
        s=gra(X,wP); r=rank(s); cnt+=(r<=k); a=agree(s,sM); rh.append(a["rho"]); ov.append(a["top20"]); ovP.append(100*len(set(r[r<=k].index)&topP0)/k)
    p=cnt/1000; ptop[w]=p; core=set(p[p>=0.95].index); stable=set(p[p>=0.80].index)
    mc[w]=dict(rho_vs_ref_median=float(np.median(rh)),rho_P5=float(np.percentile(rh,5)),rho_P95=float(np.percentile(rh,95)),
      top20_vs_ref_median=float(np.median(ov)),top20_vs_unperturbed_median=float(np.median(ovP)),
      robust_core_p95=len(core),core_in_ref_top20=len(core&topM),stable_p80=len(stable),stable_in_ref_top20=len(stable&topM))
out["montecarlo"]=mc; pd.DataFrame(ptop).to_csv(OUT+"l053_montecarlo_ptop20.csv")
# ---- (3) spatial autocorrelation
from libpysal.weights import KNN; from esda.moran import Moran
W=KNN.from_array(T[["x","y"]].values,k=6); W.transform="r"; np.random.seed(1)
wP=combined_w(Pm); shift=(rank(gra(Pm,wP))-rank(gra(Mm,wP))).values
sp={}
for nm,v in [("logres_T1",np.log(T.met_total_mean/T.proxy_total_mean).values),("logres_T1c",loc.values),("rank_shift_T1c_objective",shift),("metered_total",T.met_total_mean.values),("form_factor",T.C7_form_factor.values)]:
    m=Moran(v,W,permutations=999); sp[nm]=dict(I=round(float(m.I),3),p_sim=float(m.p_sim))
out["spatial"]=sp
json.dump(out,open(OUT+"l053_noise_mc_spatial.json","w"),indent=1); print(json.dumps(out,indent=1))
