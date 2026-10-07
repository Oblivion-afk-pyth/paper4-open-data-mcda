"""Robustness: (1) Monte Carlo ±20% multiplicative noise on proxy energy criteria (C1, C2, C5), 1,000 runs, T1c;
(2) weighting x method sensitivity table, T1c vs metered T0."""
import pandas as pd, numpy as np, sys, json
sys.path.insert(0,"scripts"); from mcda import *
P=pd.read_csv("03_outputs/matrix_proxy_T1c.csv",index_col=0); M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0)
E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]; n=len(P); k=int(round(0.2*n))
rng=np.random.default_rng(2026); out={}
for wname in ["objective","equal"]:
    wM=combined_w(M) if wname=="objective" else pd.Series(1/6,index=M.columns)
    rM=rank(gra(M,wM)); topM=set(rM[rM<=k].index)
    rhos,ovl=[],[]; intop=pd.Series(0,index=P.index)
    for i in range(1000):
        X=P.copy(); X[E]=X[E]*rng.uniform(0.8,1.2,size=(n,3))
        w=combined_w(X) if wname=="objective" else pd.Series(1/6,index=X.columns)
        s=gra(X,w); r=rank(s); top=r<=k; intop+=top
        c=compare(s,gra(M,wM)); rhos.append(c["spearman"]); ovl.append(c["top20_overlap_pct"])
    p=intop/1000
    out[wname]=dict(rho_median=float(np.median(rhos)),rho_p5=float(np.percentile(rhos,5)),rho_p95=float(np.percentile(rhos,95)),
        top20_median=float(np.median(ovl)),top20_p5=float(np.percentile(ovl,5)),top20_p95=float(np.percentile(ovl,95)),
        lsoas_top20_in_95pct_runs=int((p>=0.95).sum()),lsoas_top20_in_50_95pct=int(((p>=0.5)&(p<0.95)).sum()),
        of_stable_top_also_metered_top=int(len(set(p[p>=0.95].index)&topM)))
    p.rename("p_top20").to_csv(f"03_outputs/montecarlo_p_top20_{wname}.csv")
json.dump(out,open("03_outputs/montecarlo_summary.json","w"),indent=1)
# weighting x method table
W={"Entropy":(entropy_w(P),entropy_w(M)),"CRITIC":(critic_w(P),critic_w(M)),"Entropy×CRITIC":(combined_w(P),combined_w(M)),
   "Equal":(pd.Series(1/6,index=P.columns),)*2}
rows=[]
for wn,(wp,wm) in W.items():
    for mn,f in [("GRA",gra),("TOPSIS",topsis),("VIKOR",vikor)]:
        c=compare(f(P,wp),f(M,wm)); rows.append(dict(weights=wn,method=mn,rho=c["spearman"],kendall=c["kendall"],top20=c["top20_overlap_pct"],mean_shift=c["mean_abs_rank_shift"]))
T=pd.DataFrame(rows); T.to_csv("03_outputs/sensitivity_weights_methods_T1c.csv",index=False)
# method-vs-method on metered alone (reference for how much method choice matters)
wm=combined_w(M); ref=[dict(pair=a+" vs "+b,**compare(fa(M,wm),fb(M,wm))) for (a,fa),(b,fb) in [(("GRA",gra),("TOPSIS",topsis)),(("GRA",gra),("VIKOR",vikor)),(("TOPSIS",topsis),("VIKOR",vikor))]]
pd.DataFrame(ref).to_csv("03_outputs/sensitivity_method_vs_method_metered.csv",index=False)
print(json.dumps(out,indent=1)); print(T.to_string(index=False)); print(pd.DataFrame(ref).to_string(index=False))
