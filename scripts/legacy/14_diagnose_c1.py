"""RQ4 diagnosis: what explains the gap between proxy and metered energy intensity (C1) and total energy per dwelling?"""
import pandas as pd, numpy as np
L=pd.read_csv("03_outputs/level1_lsoa_estimates_vs_metered.csv",index_col=0)
h=pd.read_parquet("02_processed/leeds_dwelling_predictions.parquet")
def census():
    a=pd.read_csv("02_processed/leeds_lsoa_census_ts017.csv").set_index("geography code"); c=a.columns
    n=a[c[2]]-a[c[3]]; sizes=np.array([1,2,3,4,5,6,7,8])
    hh=(a[c[4:12]].values*sizes).sum(1)/n
    t=pd.read_csv("02_processed/leeds_lsoa_census_ts054.csv").set_index("geography code"); tc=t.columns
    o=pd.read_csv("02_processed/leeds_lsoa_census_ts052.csv").set_index("geography code"); oc=o.columns
    return pd.DataFrame({"hh_size":hh,"pct_1person":a[c[4]]/n*100,"pct_5plus":a[c[8:12]].sum(1)/n*100,
       "pct_private_rent":t[tc[11]]/t[tc[2]]*100,"pct_social_rent":t[tc[8]]/t[tc[2]]*100,"pct_owned":t[tc[3]]/t[tc[2]]*100,
       "pct_overcrowded":(o[oc[6]]+o[oc[7]])/o[oc[2]]*100,"pct_underoccupied":o[oc[3]]/o[oc[2]]*100,"households":n})
G=h.groupby("lsoa21cd")
X=census().join(pd.DataFrame({"pct_flat":G.PROP_TYPE.apply(lambda s:(s=="Flat").mean()*100),
   "pct_pre1930":G.PROP_AGE_BAND.apply(lambda s:(s==1).mean()*100),"pct_FG":G.EPC.apply(lambda s:(s=="F/G").mean()*100),
   "mean_tfa":G.tfa_m2.mean(),"imd_quint":G.IMD_BAND_ENG.mean()}))
X["epc_coverage"]=L.n_epc/X.households*100
X["gas_share_gap_pp"]=(L.gas_share_epc-L.met_gas_share)*100
Y=pd.DataFrame({"ratio_total":L.proxy_total_mean/L.met_total_mean,"ratio_gas":L.proxy_gas_mean/L.met_gas_mean,"ratio_elec":L.proxy_elec_mean/L.met_elec_mean})
Y["log_ratio_total"]=np.log(Y.ratio_total)
D=X.join(Y).replace([np.inf,-np.inf],np.nan).dropna()
corr=D.corr(method="spearman")[["ratio_total","ratio_gas","ratio_elec"]].drop(["ratio_total","ratio_gas","ratio_elec","log_ratio_total"]).round(2).sort_values("ratio_total")
print("Spearman correlation of proxy/metered ratio with LSOA characteristics\n",corr.to_string())
# multivariate standardised OLS on log ratio
from numpy.linalg import lstsq
feats=[c for c in X.columns if c not in("households",)]
Z=(D[feats]-D[feats].mean())/D[feats].std(); Z.insert(0,"const",1.0)
b,*_=lstsq(Z.values,D.log_ratio_total.values,rcond=None); pred=Z.values@b
r2=1-((D.log_ratio_total-pred)**2).sum()/((D.log_ratio_total-D.log_ratio_total.mean())**2).sum()
print("\nStandardised OLS on log(proxy/metered total), R2=%.2f"%r2); print(pd.Series(b[1:],index=feats).round(3).sort_values().to_string())
D.to_csv("03_outputs/rq4_c1_diagnosis_lsoa.csv"); corr.to_csv("03_outputs/rq4_c1_diagnosis_corr.csv")
print("\nratio_total describe:",Y.ratio_total.describe().round(3).to_dict())
