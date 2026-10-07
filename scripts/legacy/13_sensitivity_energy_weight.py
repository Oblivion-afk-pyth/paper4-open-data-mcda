"""Stress test: does agreement hold when the energy criteria (the only ones that differ) carry more weight?"""
import pandas as pd, numpy as np, sys
sys.path.insert(0,"scripts"); from mcda import *
P=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0); M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0)
E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]
rows=[]
eq=pd.Series(1/6,index=P.columns)
rows.append(dict(case="equal weights (energy = 50%)",**compare(gra(P,eq),gra(M,eq))))
for share in [0.5,0.7,0.9]:
    w=pd.Series({c:(share/3 if c in E else (1-share)/3) for c in P.columns})
    rows.append(dict(case=f"energy criteria = {int(share*100)}% of weight",**compare(gra(P,w),gra(M,w))))
we=combined_w(M[E]); rows.append(dict(case="energy-only (C1,C2,C5), objective weights",**compare(gra(P[E],we),gra(M[E],we))))
for c in E: rows.append(dict(case=f"single criterion {c}",**compare(P[c],M[c])))
R=pd.DataFrame(rows); R.to_csv("03_outputs/level2_energy_weight_stress.csv",index=False)
