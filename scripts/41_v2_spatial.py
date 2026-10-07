"""v2 spatial dependence (Leeds): Moran's I (queen contiguity, row-standardised, 999 permutations) for proxy residuals and rank
shifts; RQ4 regression of log(T1/metered) re-estimated as OLS and spatial error model (ML) if residual autocorrelation is significant."""
import pandas as pd, numpy as np, geopandas as gpd, json, sys, warnings; warnings.filterwarnings("ignore")
from libpysal.weights import Queen; from esda.moran import Moran; import spreg
sys.path.insert(0,"scripts"); from mcda import gra, combined_w; from mcda_v2 import *
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); C=A[A.la=="E08000035"].copy()
g=gpd.read_file("02_processed/leeds_lsoa_2021.gpkg").set_index("lsoa21cd").loc[C.index]
W=Queen.from_dataframe(g,use_index=True); W.transform="r"
C["res_T1"]=np.log(C.proxy_total_mean/C.met_total_mean); C["res_T1c"]=np.log(C.proxyc_total_mean/C.met_total_mean)
M=pd.read_csv("03_outputs/v2/matrix_leeds_T0.csv",index_col=0).loc[C.index]; eq=pd.Series(1/6,index=M.columns); rM=rank(gra(M,eq))
for t in ["T1","T1c"]:
    P=pd.read_csv(f"03_outputs/v2/matrix_leeds_{t}.csv",index_col=0).loc[C.index]; C[f"shift_{t}"]=rank(gra(P,eq))-rM
out={}
np.random.seed(1)
for v in ["res_T1","res_T1c","shift_T1","shift_T1c"]:
    m=Moran(C[v].values,W,permutations=999); out[v]=dict(I=round(float(m.I),3),p_sim=float(m.p_sim),z=round(float(m.z_sim),2))
F=["hh_size","pct_1person","pct_private_rent","pct_social_rent","pct_overcrowded","pct_underoccupied","imd_score","mean_tfa","gas_share_epc","pct_flat","pct_pre1930","pct_FG","epc_coverage"]
C["gas_gap_pp"]=(C.gas_share_epc-C.met_gas_share)*100; F=F+["gas_gap_pp"]
Z=((C[F]-C[F].mean())/C[F].std()).values; y=C.res_T1.values.reshape(-1,1)
ols=spreg.OLS(y,Z,w=W,spat_diag=True,moran=True,name_x=F,name_y="log(T1/metered)")
em=spreg.ML_Error(y,Z,w=W,name_x=F,name_y="log(T1/metered)")
coef=pd.DataFrame({"OLS_beta":ols.betas.flatten()[1:],"OLS_p":[p for _,p in ols.t_stat[1:]],"SEM_beta":em.betas.flatten()[1:-1],"SEM_p":[p for _,p in em.z_stat[1:-1]]},index=F).round(3)
coef.to_csv("03_outputs/v2/rq4_regression_ols_sem.csv")
out["OLS_R2"]=round(float(ols.r2),3); out["OLS_residual_MoranI"]=[round(float(x),3) for x in ols.moran_res[:2]]; out["SEM_lambda"]=round(float(em.lam),3); out["SEM_pseudoR2"]=round(float(em.pr2),3)
out["LM_error"]=[round(float(x),3) for x in ols.lm_error]; out["LM_lag"]=[round(float(x),3) for x in ols.lm_lag]
C[["res_T1","res_T1c","shift_T1","shift_T1c"]].to_csv("03_outputs/v2/rq4_residuals_shifts.csv")
json.dump(out,open("03_outputs/v2/spatial_v2.json","w"),indent=1); print(json.dumps(out,indent=1)); print(coef.to_string())
