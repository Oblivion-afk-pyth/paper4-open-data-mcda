"""Leeds 053 validation: RQ1 BIM plausibility checks; Level 1 prediction vs metered (postcode); Level 2 decision agreement
proxy vs meter-informed reference with FIXED weights (from proxy matrix); six (C1-C6) vs eight (C1-C8 incl. BIM) criteria;
weights/method/criterion-removal sensitivity; postcode bootstrap CIs; RQ3 form-factor association with metered intensity."""
import os,sys,json,numpy as np,pandas as pd,geopandas as gpd
from scipy.stats import spearmanr,kruskal
D=(__import__("paths").ROOT+""); O=D+"02_processed/v4_district/"; OUT=D+"03_outputs/v4_district/"
sys.path.insert(0,D+"scripts"); from mcda import gra,topsis,vikor,combined_w; from mcda_v2 import matrix,agree,energy_w,rank
T=pd.read_csv(O+"l053_postcode_table.csv",index_col=0); T=T[T.keep]; res={}
# ---- RQ1: BIM plausibility
b=gpd.read_file(O+"l053_buildings_v2.gpkg"); b1=b[b.lidar_ok&(b.n_epc==1)&b.built_form.notna()]
grp={k:v.exposed_perim_m.values for k,v in b1.groupby("built_form") if len(v)>=20}
res["RQ1"]=dict(buildings=len(b),lidar_ok=int(b.lidar_ok.sum()),single_epc=int((b.n_epc==1).sum()),
  exposed_perim_median_by_form={k:round(float(np.median(v)),1) for k,v in grp.items()},kruskal_p=float(kruskal(*grp.values()).pvalue),
  tfa_vs_footprint_x_storeys_rho=round(float(spearmanr(b1.epc_tfa_m2,b1.area_m2*b1.storeys_est).correlation),3),
  tfa_over_footprint_median=round(float((b1.epc_tfa_m2/b1.area_m2).median()),2))
# ---- Level 1
def l1(p,o):
    k=p.notna()&o.notna()&(o>0); p,o=p[k],o[k]
    return dict(n=int(k.sum()),MAPE=round(float(100*(abs(p-o)/o).mean()),1),R2=round(float(1-((o-p)**2).sum()/((o-o.mean())**2).sum()),3),bias=round(float(100*(p.sum()-o.sum())/o.sum()),1),rho=round(float(spearmanr(p,o).correlation),3))
L={}
for v,c in [("T1","proxy"),("T1c","proxyc")]:
    L[f"total_{v}"]=l1(T[f"{c}_total_mean"],T.met_total_mean); L[f"gas_{v}"]=l1(T[f"{c}_gas_mean"],T.met_gas_mean); L[f"elec_{v}"]=l1(T[f"{c}_elec_mean"],T.met_elec_mean)
res["Level1"]=L
# ---- matrices
BIM=["C7_form_factor","C8_pv_area_dw"]
def mat(src,eight):
    X=matrix(T,src)
    if eight: X=X.join(T[BIM])
    return X
rows=[]; wv={}
def scen(tier,eight,w,method=gra,drop=None,energy_only=False,label=None):
    P,M=mat(tier,eight),mat("M",eight)
    if energy_only: keep=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]; P,M=P[keep],M[keep]
    if drop: P,M=P.drop(columns=drop),M.drop(columns=drop)
    wP=combined_w(P) if w=="objective" else (pd.Series(1/P.shape[1],index=P.columns) if w=="equal" else energy_w(P.columns,{"e70":0.7,"e90":0.9}[w]))
    sP,sM=method(P,wP),method(M,wP)
    lab=label or f"{tier} {'eight' if eight else 'six'} criteria"+(f" excl. {drop}" if drop else "")+(" energy-only" if energy_only else "")
    wv[f"{lab}|{w}"]={k:round(float(x),3) for k,x in wP.items()}
    r=dict(case=lab,weights=w,method=method.__name__,n=len(P),**agree(sP,sM)); rows.append(r); return sP,sM
main={}
for tier in ["T1","T1c"]:
    for eight in [False,True]:
        for w in ["objective","equal","e70","e90"]:
            main[(tier,eight,w)]=scen(tier,eight,w)
for eight in [False,True]:
    for m in [topsis,vikor]:
        for w in ["objective","equal"]: scen("T1c",eight,w,method=m)
    for w in ["objective","equal"]: scen("T1c",eight,w,energy_only=True,label="T1c energy criteria only (C1,C2,C5)") if not eight else None
for w in ["objective","equal","e70"]:
    for d in ["C1_energy_intensity","C3_fuel_poverty","C4_income_deprivation","C6_stock_homogeneity","C7_form_factor","C8_pv_area_dw"]:
        scen("T1c",True,w,drop=[d])
    scen("T1c",True,w,drop=["C3_fuel_poverty","C4_income_deprivation"])
R=pd.DataFrame(rows).drop_duplicates(subset=["case","weights","method"])
# bootstrap CIs (postcodes resampled) for main T1c GRA scenarios
rng=np.random.default_rng(11); boot=[]
k=int(round(0.2*len(T)))
for eight in [False,True]:
    for w in ["objective","equal","e70","e90"]:
        sP,sM=main[("T1c",eight,w)]; rP,rM=rank(sP),rank(sM); tP,tM=(rP<=k).values,(rM<=k).values; st=[]
        for _ in range(1000):
            i=rng.integers(0,len(sP),len(sP)); st.append((spearmanr(sP.values[i],sM.values[i]).correlation,100*(tP[i]&tM[i]).sum()/max(tM[i].sum(),1)))
        st=np.array(st); boot.append(dict(case=f"T1c {'eight' if eight else 'six'}",weights=w,rho_CI=[round(x,3) for x in np.nanpercentile(st[:,0],[2.5,97.5])],top20_CI=[round(x,1) for x in np.nanpercentile(st[:,1],[2.5,97.5])]))
# RQ3: does BIM change the priority list; is form factor associated with metered intensity
rq3={}
for w in ["objective","equal"]:
    s6=main[("T1c",False,w)][0]; s8=main[("T1c",True,w)][0]; rq3[f"six_vs_eight_proxy|{w}"]=agree(s8,s6)
    m6=main[("T1c",False,w)][1]; m8=main[("T1c",True,w)][1]; rq3[f"six_vs_eight_reference|{w}"]=agree(m8,m6)
mi=T.met_total_mean/T.mean_tfa
def resid(y,x): x=np.c_[np.ones(len(x)),x]; return y-x@np.linalg.lstsq(x,y,rcond=None)[0]
rq3["rho_formfactor_metered_intensity"]=round(float(spearmanr(T.C7_form_factor,mi).correlation),3)
rq3["rho_formfactor_metered_total"]=round(float(spearmanr(T.C7_form_factor,T.met_total_mean).correlation),3)
rq3["partial_rho_formfactor_intensity|EPC_primary"]=round(float(spearmanr(resid(T.C7_form_factor.rank().values,T.mean_epc_primary.rank().values),resid(mi.rank().values,T.mean_epc_primary.rank().values)).correlation),3)
rq3["rho_EPCprimary_metered_intensity"]=round(float(spearmanr(T.mean_epc_primary,mi).correlation),3)
rq3["rho_pv_area_metered_elec"]=round(float(spearmanr(T.C8_pv_area_dw,T.met_elec_mean).correlation),3)
res["RQ3"]=rq3; res["bootstrap"]=boot
R.to_csv(OUT+"l053_decision_validation.csv",index=False); json.dump(res,open(OUT+"l053_validation.json","w"),indent=1); json.dump(wv,open(OUT+"l053_weight_vectors.json","w"),indent=1)
mat("T1c",True).to_csv(OUT+"l053_matrix_T1c.csv"); mat("M",True).to_csv(OUT+"l053_matrix_T0.csv"); mat("T1",True).to_csv(OUT+"l053_matrix_T1.csv")
M8=mat("M",True); M8.corr(method="spearman").round(2).to_csv(OUT+"l053_criteria_corr_spearman.csv")
pd.set_option("display.width",250); print(json.dumps({k:res[k] for k in ["RQ1","Level1","RQ3"]},indent=0)); print(R.to_string(index=False)); print(json.dumps(boot))
print(M8.corr(method="spearman").round(2).to_string())
