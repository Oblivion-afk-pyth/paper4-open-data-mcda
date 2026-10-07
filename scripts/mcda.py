"""Objective-weighted MCDA toolkit: entropy, CRITIC, combined weights; GRA, TOPSIS, VIKOR (all criteria benefit-type)."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau
def minmax(X): return (X-X.min())/(X.max()-X.min())
def entropy_w(X):
    P=X/X.sum(); m=len(X); E=-(P*np.log(P.where(P>0,1))).sum()/np.log(m); d=1-E; return d/d.sum()
def critic_w(X):
    Z=minmax(X); C=Z.std()*(1-Z.corr()).sum(); return C/C.sum()
def combined_w(X):
    g=np.sqrt(entropy_w(X)*critic_w(X)); return g/g.sum()
def gra(X,w,xi=0.5):
    D=(1-minmax(X)).abs(); c=(D.values.min()+xi*D.values.max())/(D+xi*D.values.max()); return (c*w).sum(axis=1)
def topsis(X,w):
    V=X/np.sqrt((X**2).sum())*w; dp=np.sqrt(((V-V.max())**2).sum(1)); dn=np.sqrt(((V-V.min())**2).sum(1)); return dn/(dp+dn)
def vikor(X,w,v=0.5):
    f=(X.max()-X)/(X.max()-X.min()); S=(w*f).sum(1); R=(w*f).max(1)
    Q=v*(S-S.min())/(S.max()-S.min())+(1-v)*(R-R.min())/(R.max()-R.min()); return 1-Q   # higher = better priority
def rank(s): return s.rank(ascending=False,method="first").astype(int)
def compare(a,b,top=0.2):
    ra,rb=rank(a),rank(b); k=int(round(top*len(a)))
    ta,tb=set(ra[ra<=k].index),set(rb[rb<=k].index)
    return dict(spearman=round(spearmanr(a,b).correlation,3),kendall=round(kendalltau(a,b).correlation,3),
                top20_overlap_pct=round(100*len(ta&tb)/k,1),mean_abs_rank_shift=round(float((ra-rb).abs().mean()),1),
                max_rank_shift=int((ra-rb).abs().max()))
