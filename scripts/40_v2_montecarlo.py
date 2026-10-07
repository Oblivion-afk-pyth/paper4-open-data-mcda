"""v2 Monte Carlo for Leeds T1c. Energy error is applied ONCE per LSOA as a multiplicative factor exp(e) to the corrected
energy estimate, so C1, C2 and C5 move together (correlated). Three error models: (A) independent uniform ±20% (v1, for
comparison); (B) independent draws from the empirical out-of-fold LOLAO residuals of the correction model; (C) spatially
correlated normal errors e = u_MSOA + eps, with SDs from a one-way random-effects decomposition of the same residuals."""
import pandas as pd, numpy as np, json, sys
sys.path.insert(0,"scripts"); from mcda import gra, combined_w; from mcda_v2 import *
rng=np.random.default_rng(2026); R=1000
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); C=A[A.la=="E08000035"]
P=pd.read_csv("03_outputs/v2/matrix_leeds_T1c.csv",index_col=0); M=pd.read_csv("03_outputs/v2/matrix_leeds_T0.csv",index_col=0)
dec=json.load(open("03_outputs/v2/correction_validation.json"))["resid_decomposition"]; oof=A.oof_total.dropna().values
msoa=C.loc[P.index,"msoa21cd"].values; um=np.unique(msoa); n=len(P); k=int(round(0.2*n)); E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]
out={}; ptop={}
for w in ["objective","equal"]:
    wM=combined_w(M) if w=="objective" else pd.Series(1/6,index=M.columns); sM=gra(M,wM); topM=set(rank(sM)[rank(sM)<=k].index)
    for model in ["A_uniform20","B_empirical_iid","C_empirical_spatial"]:
        rhos,ovl=[],[]; cnt=pd.Series(0,index=P.index)
        for i in range(R):
            if model=="A_uniform20": f=pd.DataFrame(rng.uniform(0.8,1.2,(n,3)),index=P.index,columns=E)
            else:
                if model=="B_empirical_iid": e=rng.choice(oof,n,replace=True)
                else:
                    u=dict(zip(um,rng.normal(0,dec["sd_between_msoa"],len(um)))); e=np.array([u[m] for m in msoa])+rng.normal(0,dec["sd_within"],n)
                f=pd.DataFrame({c:np.exp(e) for c in E},index=P.index)
            X=P.copy(); X[E]=X[E]*f
            wP=combined_w(X) if w=="objective" else pd.Series(1/6,index=X.columns)
            s=gra(X,wP); r=rank(s); a=agree(s,sM); rhos.append(a["rho"]); ovl.append(a["top20"]); cnt+=(r<=k)
        p=cnt/R; ptop[f"{w}|{model}"]=p
        core=set(p[p>=0.95].index)
        out[f"{w}|{model}"]=dict(rho_median=float(np.median(rhos)),rho_P5=float(np.percentile(rhos,5)),rho_P95=float(np.percentile(rhos,95)),
            top20_median=float(np.median(ovl)),top20_P5=float(np.percentile(ovl,5)),top20_P95=float(np.percentile(ovl,95)),
            robust_core=len(core),core_in_reference_top20=len(core&topM))
pd.DataFrame(ptop).to_csv("03_outputs/v2/montecarlo_ptop20_v2.csv"); json.dump(out,open("03_outputs/v2/montecarlo_v2.json","w"),indent=1); print(json.dumps(out,indent=1))
