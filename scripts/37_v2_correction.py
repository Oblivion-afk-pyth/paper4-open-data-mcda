"""v2 area-level correction. Validation: random 5-fold (reference), leave-one-local-authority-out (LOLAO), spatial-block 10-fold
(k-means on LSOA centroids). Out-of-fold LOLAO residuals kept for the empirical Monte Carlo. Final models: (i) trained on all
non-Leeds LSOAs -> Leeds; (ii) trained on all LSOAs except Leeds and Bradford -> Bradford."""
import pandas as pd, numpy as np, lightgbm as lgb, geopandas as gpd, json, glob
from sklearn.model_selection import KFold, LeaveOneGroupOut, GroupKFold, cross_val_predict
from sklearn.cluster import KMeans
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0)
F=["hh_size","pct_1person","pct_private_rent","pct_social_rent","pct_overcrowded","pct_underoccupied","imd_score","income_score","mean_tfa","gas_share_epc","pct_flat","pct_pre1930","pct_FG","pct_AB","mean_epc_primary","epc_coverage"]
for k in ["total","gas","elec"]: A[f"y_{k}"]=np.log(A[f"met_{k}_mean"]/A[f"proxy_{k}_mean"])
g=gpd.read_file([f for f in glob.glob("01_raw/boundaries/*.gpkg") if "(1)" not in f][0]); code=[c for c in g.columns if c.upper().startswith("LSOA21CD")][0]
g=g[g[code].isin(A.index)].set_index(code).to_crs(27700); cen=g.geometry.centroid
A["x"]=cen.x; A["y"]=cen.y
A["block"]=KMeans(10,n_init=10,random_state=1).fit_predict(A[["x","y"]].fillna(A[["x","y"]].mean()))
A.to_csv("02_processed/v2/lsoa_table_v2.csv")
mk=lambda: lgb.LGBMRegressor(n_estimators=300,learning_rate=0.03,num_leaves=15,min_child_samples=30,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,verbose=-1,n_jobs=2,random_state=1)
cal=A[A.la!="E08000035"]; res={}
def r2(y,p): return round(float(1-((y-p)**2).sum()/((y-y.mean())**2).sum()),3)
for k in ["total","gas","elec"]:
    c=cal.dropna(subset=F+[f"y_{k}"]); y=c[f"y_{k}"]
    p_rand=cross_val_predict(mk(),c[F],y,cv=KFold(5,shuffle=True,random_state=1))
    p_lola=cross_val_predict(mk(),c[F],y,cv=LeaveOneGroupOut(),groups=c.la)
    p_blk=cross_val_predict(mk(),c[F],y,cv=GroupKFold(10),groups=c.block)
    res[k]=dict(n=len(c),n_la=int(c.la.nunique()),R2_random5=r2(y,p_rand),R2_LOLAO=r2(y,p_lola),R2_spatial_block10=r2(y,p_blk),
               sd_y=round(float(y.std()),4),sd_resid_LOLAO=round(float((y-p_lola).std()),4))
    A.loc[c.index,f"oof_{k}"]=y-p_lola
    # final Leeds model
    m=mk().fit(c[F],y); L=A.la=="E08000035"; A.loc[L,f"proxyc_{k}_mean"]=A.loc[L,f"proxy_{k}_mean"]*np.exp(m.predict(A.loc[L,F]))
    cb=c[c.la!="E08000032"]; mb=mk().fit(cb[F],cb[f"y_{k}"]); B=A.la=="E08000032"; A.loc[B,f"proxyc_{k}_mean"]=A.loc[B,f"proxy_{k}_mean"]*np.exp(mb.predict(A.loc[B,F]))
# variance decomposition of OOF total residual into MSOA-level and LSOA-level components (one-way random effects, method of moments)
e=A.dropna(subset=["oof_total","msoa21cd"]); grp=e.groupby("msoa21cd").oof_total
nbar=grp.size().mean(); msb=(grp.size()*(grp.mean()-e.oof_total.mean())**2).sum()/(grp.ngroups-1); msw=((e.oof_total-grp.transform("mean"))**2).sum()/(len(e)-grp.ngroups)
s2b=max((msb-msw)/nbar,0); res["resid_decomposition"]=dict(sd_between_msoa=round(float(np.sqrt(s2b)),4),sd_within=round(float(np.sqrt(msw)),4),icc=round(float(s2b/(s2b+msw)),3))
A.to_csv("02_processed/v2/lsoa_table_v2.csv"); json.dump(res,open("03_outputs/v2/correction_validation.json","w"),indent=1); print(json.dumps(res,indent=1))
