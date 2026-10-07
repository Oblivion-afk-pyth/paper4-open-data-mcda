"""Figure 2 re-layout for print: (a) on top, (b) and (c) side by side below."""
import pandas as pd, geopandas as gpd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
S=pd.read_csv("03_outputs/rq4_rank_shift_equal_weights.csv",index_col=0)
g=gpd.read_file("02_processed/leeds_lsoa_2021.gpkg").set_index("lsoa21cd").join(S)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9})
fig=plt.figure(figsize=(7.2,7.4)); gs=fig.add_gridspec(2,2,height_ratios=[1.15,1],hspace=0.12,wspace=0.05)
a=fig.add_subplot(gs[0,:]); b=fig.add_subplot(gs[1,0]); c=fig.add_subplot(gs[1,1])
g.plot(column="rank_T0",cmap="viridis_r",ax=a,legend=True,legend_kwds={"shrink":0.7,"label":"Priority rank (1 = most urgent)"},linewidth=0.05,edgecolor="white")
a.set_title("(a) Metered benchmark priority (T0)",loc="left",fontsize=10)
lim=max(abs(g.shift_T1).max(),abs(g.shift_T1c).max()); norm=TwoSlopeNorm(0,-lim,lim)
for ax,col,t in [(b,"shift_T1","(b) Rank shift, proxy T1"),(c,"shift_T1c","(c) Rank shift, proxy T1c")]:
    g.plot(column=col,cmap="RdBu",norm=norm,ax=ax,linewidth=0.05,edgecolor="white"); ax.set_title(t,loc="left",fontsize=10)
for ax in (a,b,c): ax.set_axis_off()
sm=plt.cm.ScalarMappable(cmap="RdBu",norm=norm); cb=fig.colorbar(sm,ax=[b,c],orientation="horizontal",fraction=0.05,pad=0.02,aspect=40)
cb.set_label("Proxy rank − metered rank   (red: proxy more urgent; blue: less urgent)")
plt.savefig("03_outputs/figures/fig2_rank_shift_maps_print.png",dpi=300,bbox_inches="tight")
