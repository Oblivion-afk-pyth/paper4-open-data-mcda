"""Figure: RQ3 data-reduction curve (ranking agreement vs metered benchmark)."""
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=pd.read_csv("03_outputs/rq3_data_reduction_curve.csv")
lab={"T1c":"T1c\nfull + area\ncorrection","T1":"T1\nfull open\nproxies","T2":"T2\nproperty\nregister","T3":"T3\nhousing\ntypology","T4":"T4\ndeprivation\nonly*"}
x=range(len(R)); BLUE,ORANGE,INK,MUTED="#2a78d6","#eb6834","#1f1f1e","#8a897f"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.edgecolor":MUTED,"axes.labelcolor":INK,"xtick.color":INK,"ytick.color":INK})
fig,ax=plt.subplots(1,2,figsize=(10,3.9))
for a,(co,ce,thr,yl,ttl) in zip(ax,[("rho_objW","rho_eqW",0.80,"Spearman ρ vs metered ranking","(a) Rank correlation"),
                                    ("top20_objW","top20_eqW",70,"Top-20% LSOAs shared with metered (%)","(b) Top-priority overlap")]):
    a.axhline(thr,color=MUTED,lw=1,ls=(0,(4,3)),zorder=1); a.text(len(R)-0.55,thr,"pass mark",va="bottom",ha="right",color=MUTED,fontsize=8)
    for c,col,name in [(co,BLUE,"Objective weights"),(ce,ORANGE,"Equal weights")]:
        a.plot(x,R[c],color=col,lw=2,marker="o",ms=8,mec="white",mew=2,label=name,zorder=3)
        a.annotate(f"{R[c].iloc[0]:.2f}" if thr<1 else f"{R[c].iloc[0]:.0f}",(0,R[c].iloc[0]),xytext=(-8,0),textcoords="offset points",ha="right",va="center",color=INK,fontsize=8)
        a.annotate(f"{R[c].iloc[-1]:.2f}" if thr<1 else f"{R[c].iloc[-1]:.0f}",(len(R)-1,R[c].iloc[-1]),xytext=(8,0),textcoords="offset points",ha="left",va="center",color=INK,fontsize=8)
    a.set_xticks(list(x)); a.set_xticklabels([lab[t] for t in R.tier],fontsize=8); a.set_ylabel(yl); a.set_title(ttl,loc="left",fontsize=10,color=INK)
    a.set_ylim(0,1.02) if thr<1 else a.set_ylim(0,102); a.set_xlim(-0.6,len(R)-0.4)
    a.grid(axis="y",color="#e4e3dc",lw=0.8,zorder=0); a.spines[["top","right"]].set_visible(False)
ax[0].legend(frameon=False,loc="lower left",fontsize=8)
fig.text(0.01,-0.04,"Leeds, 488 LSOAs, grey relational analysis. *T4 has no stock data, so criterion C6 is dropped.",fontsize=8,color=MUTED)
plt.tight_layout(); plt.savefig("03_outputs/figures/fig_rq3_data_reduction_curve.png",dpi=300,bbox_inches="tight")
