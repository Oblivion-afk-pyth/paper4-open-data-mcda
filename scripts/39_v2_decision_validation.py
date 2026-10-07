"""v2 decision validation, Leeds and Bradford. Main comparison uses FIXED weights (the same vector for proxy and reference),
derived from the proxy matrix so the proxy decision uses proxy information only; own-weights variant reported alongside."""
import pandas as pd, numpy as np, json, sys
sys.path.insert(0,"scripts"); from mcda import gra, topsis, vikor, combined_w, entropy_w, critic_w; from mcda_v2 import *
rng=np.random.default_rng(11); B=1000; OUT="03_outputs/v2/"
def ld(city,nm,suf=""): return pd.read_csv(f"{OUT}matrix_{city}_{nm}{suf}.csv",index_col=0)
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0)
rows=[]; boot=[]; wv={}
for city in ["leeds","bradford"]:
    M=ld(city,"T0"); msoa=A.loc[M.index,"msoa21cd"]
    def scen(P,Mx,label,wname,wfix=None,method=gra,own=False):
        if wname=="objective": wP=combined_w(P); wM=combined_w(Mx) if own else wP
        else: wP=wM=energy_w(P.columns,{"equal":None,"e70":0.7,"e90":0.9}[wname]) if wname!="equal" else pd.Series(1/P.shape[1],index=P.columns)
        wv[f"{city}|{label}|{wname}"]={k:round(float(v),3) for k,v in wP.items()}
        sP,sM=method(P,wP),method(Mx,wM); r=dict(city=city,case=label,weights=wname,own_weights=own,method=method.__name__,**agree(sP,sM)); rows.append(r); return sP,sM
    for tier in ["T1","T1c"]:
        P=ld(city,tier)
        for w in ["objective","equal","e70","e90"]:
            sP,sM=scen(P,M,f"{tier} six criteria",w)
            if tier=="T1c" and city=="leeds":   # MSOA cluster bootstrap
                ra,rb=rank(sP),rank(sM); k=int(round(0.2*len(ra))); topM=rb<=k; topP=ra<=k; ms=msoa.unique()
                st=[]
                for b in range(B):
                    pick=rng.choice(ms,len(ms),replace=True); idx=np.concatenate([np.where(msoa.values==m)[0] for m in pick])
                    a_,b_=sP.values[idx],sM.values[idx]; tm=topM.values[idx]
                    from scipy.stats import spearmanr,kendalltau
                    st.append((spearmanr(a_,b_).correlation,kendalltau(a_,b_).correlation,100*(topP.values[idx]&tm).sum()/max(tm.sum(),1)))
                st=np.array(st); boot.append(dict(city=city,case="T1c six criteria GRA",weights=w,rho_CI=[round(x,3) for x in np.percentile(st[:,0],[2.5,97.5])],tau_CI=[round(x,3) for x in np.percentile(st[:,1],[2.5,97.5])],top20_CI=[round(x,1) for x in np.percentile(st[:,2],[2.5,97.5])]))
        if tier=="T1c":
            scen(P,M,"T1c six criteria","objective",own=True)
            for meth in [topsis,vikor]:
                for w in ["objective","equal"]: scen(P,M,"T1c six criteria",w,method=meth)
    Pc=ld(city,"T1c")
    for w in ["objective","equal","e70"]:
        scen(Pc.drop(columns="C1_energy_intensity"),M.drop(columns="C1_energy_intensity"),"T1c excl. C1",w)
        scen(ld(city,"T1c","_c1total"),ld(city,"T0","_c1total"),"T1c C1 = total energy",w)
        scen(Pc.drop(columns="C3_fuel_poverty"),M.drop(columns="C3_fuel_poverty"),"T1c excl. C3",w)
        scen(Pc.drop(columns="C4_income_deprivation"),M.drop(columns="C4_income_deprivation"),"T1c excl. C4",w)
        scen(ld(city,"T1c","_att"),ld(city,"T0","_att"),"T1c C2,C5 band-attenuated savings",w)
    # effect of attenuation on the reference itself (does the savings assumption change the decision?)
    for w in ["objective","equal"]:
        wm=pd.Series(1/6,index=M.columns) if w=="equal" else combined_w(M)
        rows.append(dict(city=city,case="T0 vs T0 band-attenuated (reference sensitivity)",weights=w,own_weights=False,method="gra",**agree(gra(ld(city,"T0","_att"),wm),gra(M,wm))))
        rows.append(dict(city=city,case="T0 C1 intensity vs total (reference sensitivity)",weights=w,own_weights=False,method="gra",**agree(gra(ld(city,"T0","_c1total"),wm),gra(M,wm))))
    for a,fa in [("GRA",gra),("TOPSIS",topsis),("VIKOR",vikor)]:
        for b_,fb in [("TOPSIS",topsis),("VIKOR",vikor)]:
            if a<b_: rows.append(dict(city=city,case=f"Reference only: {a} vs {b_}",weights="objective",own_weights=False,method="-",**agree(fa(M,combined_w(M)),fb(M,combined_w(M)))))
R=pd.DataFrame(rows); R.to_csv(OUT+"decision_validation_v2.csv",index=False)
json.dump(boot,open(OUT+"bootstrap_ci_v2.json","w"),indent=1); json.dump(wv,open(OUT+"weight_vectors_v2.json","w"),indent=1)
# threshold grid on main scenarios
G=[]
for _,r in R[(R.case.str.startswith("T1"))&(R.method=="gra")&(~R.own_weights)].iterrows():
    for t in [0.70,0.80,0.90]:
        for o in [60,70,80]: G.append(dict(city=r.city,case=r.case,weights=r.weights,rho_thr=t,top20_thr=o,passes=bool(r.rho>=t and r.top20>=o)))
pd.DataFrame(G).to_csv(OUT+"threshold_grid_v2.csv",index=False)
# criteria correlations (reference, Leeds)
M=ld("leeds","T0"); M.corr(method="spearman").round(2).to_csv(OUT+"criteria_corr_spearman_leeds.csv"); M.corr().round(2).to_csv(OUT+"criteria_corr_pearson_leeds.csv")
pd.set_option("display.width",250); print(R.to_string(index=False)); print(json.dumps(boot)); print(M.corr(method="spearman").round(2).to_string())
