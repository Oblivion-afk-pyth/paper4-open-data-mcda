"""RQ4: where do proxy rankings depart from metered rankings? Maps + correlates of rank shift."""
import pandas as pd, numpy as np, geopandas as gpd, matplotlib, sys
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
sys.path.insert(0,"scripts"); from mcda import *
P=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0); Pc=pd.read_csv("03_outputs/matrix_proxy_T1c.csv",index_col=0); M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0)
eq=pd.Series(1/6,index=M.columns)
S=pd.DataFrame({"rank_T0":rank(gra(M,eq)),"rank_T1":rank(gra(P,eq)),"rank_T1c":rank(gra(Pc,eq))})
S["shift_T1"]=S.rank_T1-S.rank_T0; S["shift_T1c"]=S.rank_T1c-S.rank_T0     # negative = proxy ranks the area MORE urgent than meters
D=pd.read_csv("03_outputs/rq4_c1_diagnosis_lsoa.csv",index_col=0)
S=S.join(D); S.to_csv("03_outputs/rq4_rank_shift_equal_weights.csv")
cor=S[[c for c in D.columns if not c.startswith("ratio") and c!="log_ratio_total"]+["shift_T1","shift_T1c"]].corr(method="spearman")[["shift_T1","shift_T1c"]].drop(["shift_T1","shift_T1c"]).round(2).sort_values("shift_T1")
cor.to_csv("03_outputs/rq4_rank_shift_correlates.csv")
g=gpd.read_file("02_processed/leeds_lsoa_2021.gpkg").set_index("lsoa21cd").join(S)
fig,ax=plt.subplots(1,3,figsize=(15,5.6))
g.plot(column="rank_T0",cmap="viridis_r",ax=ax[0],legend=True,legend_kwds={"shrink":0.6,"label":"Priority rank (1 = most urgent)"},linewidth=0.05,edgecolor="white")
ax[0].set_title("(a) Metered benchmark priority (T0)",fontsize=11)
lim=max(abs(g.shift_T1).max(),abs(g.shift_T1c).max())
for i,(c,t) in enumerate([("shift_T1","(b) Rank shift, open-data proxy (T1)"),("shift_T1c","(c) Rank shift, proxy + area correction (T1c)")],1):
    g.plot(column=c,cmap="RdBu",norm=TwoSlopeNorm(0,-lim,lim),ax=ax[i],legend=True,legend_kwds={"shrink":0.6,"label":"Proxy rank − metered rank"},linewidth=0.05,edgecolor="white")
    ax[i].set_title(t,fontsize=11)
for a in ax: a.set_axis_off()
fig.suptitle("Leeds, 488 LSOAs, GRA with equal weights. Red = proxy ranks the area as more urgent than meters; blue = less urgent.",fontsize=10,y=0.04)
plt.tight_layout(); plt.savefig("03_outputs/figures/fig_rq4_rank_shift_maps.png",dpi=300,bbox_inches="tight")
print(cor.to_string()); print(S[["shift_T1","shift_T1c"]].abs().describe().round(1).to_string())
