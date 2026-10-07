"""Rank LSOAs with proxy (T1) and metered (T0) matrices; Level 2 agreement."""
import pandas as pd, sys, json
sys.path.insert(0,"scripts"); from mcda import *
P=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0); M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0)
W=pd.DataFrame({"entropy_P":entropy_w(P),"critic_P":critic_w(P),"combined_P":combined_w(P),"entropy_M":entropy_w(M),"critic_M":critic_w(M),"combined_M":combined_w(M)}).round(4)
W.to_csv("03_outputs/weights.csv"); print(W.to_string())
wP,wM=combined_w(P),combined_w(M)
S=pd.DataFrame({"GRA_P":gra(P,wP),"GRA_M":gra(M,wM),"TOPSIS_P":topsis(P,wP),"TOPSIS_M":topsis(M,wM),"VIKOR_P":vikor(P,wP),"VIKOR_M":vikor(M,wM),
                "GRA_P_fixedW":gra(P,wM)})
for c in list(S): S["rank_"+c]=rank(S[c])
S.to_csv("03_outputs/scores_and_ranks_T1_vs_T0.csv")
rows=[dict(comparison="GRA: proxy vs metered (own weights)",**compare(S.GRA_P,S.GRA_M)),
      dict(comparison="GRA: proxy vs metered (same weights)",**compare(S.GRA_P_fixedW,S.GRA_M)),
      dict(comparison="TOPSIS: proxy vs metered",**compare(S.TOPSIS_P,S.TOPSIS_M)),
      dict(comparison="VIKOR: proxy vs metered",**compare(S.VIKOR_P,S.VIKOR_M)),
      dict(comparison="metered: GRA vs TOPSIS",**compare(S.GRA_M,S.TOPSIS_M)),
      dict(comparison="metered: GRA vs VIKOR",**compare(S.GRA_M,S.VIKOR_M))]
R=pd.DataFrame(rows); R.to_csv("03_outputs/level2_rank_agreement.csv",index=False); print(R.to_string(index=False))
