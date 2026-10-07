"""v2 shared: criteria matrices and agreement statistics."""
import pandas as pd, numpy as np
from scipy.stats import spearmanr, kendalltau
EG,EE=0.18290,0.20705   # DESNZ 2024: natural gas (gross CV), UK electricity generation, kg CO2e/kWh
CRIT=["C1_energy_intensity","C2_carbon_abatement","C3_fuel_poverty","C4_income_deprivation","C5_cost_effectiveness","C6_stock_homogeneity"]
def matrix(A,src,att=False,c1_total=False):
    if src=="M": tot,gas,el,sh=A.met_total_mean,A.met_gas_mean.fillna(0),A.met_elec_mean,A.met_gas_share
    elif src=="T1": tot,gas,el,sh=A.proxy_total_mean,A.proxy_gas_mean.fillna(0),A.proxy_elec_mean,A.gas_share_epc
    else: tot,gas,el,sh=A.proxyc_total_mean,A.proxyc_gas_mean.fillna(0),A.proxyc_elec_mean,A.gas_share_epc
    ab=A.abate_att if att else A.abate; sv=A.save_att if att else A.save
    X=pd.DataFrame(index=A.index)
    X["C1_energy_intensity"]=tot if c1_total else tot/A.mean_tfa
    X["C2_carbon_abatement"]=ab*(gas*sh*EG+el*EE)/1000
    X["C3_fuel_poverty"]=A.fuel_poverty_pct; X["C4_income_deprivation"]=A.income_score
    X["C5_cost_effectiveness"]=sv*tot/A.pkg_cost_2024; X["C6_stock_homogeneity"]=A.C6_stock_homogeneity
    return X
def rank(s): return s.rank(ascending=False,method="first").astype(int)
def agree(a,b,top=0.2):
    ra,rb=rank(a),rank(b); k=int(round(top*len(a))); ta,tb=set(ra[ra<=k].index),set(rb[rb<=k].index)
    return dict(rho=round(spearmanr(a,b).correlation,3),tau=round(kendalltau(a,b).correlation,3),top20=round(100*len(ta&tb)/k,1),shift=round(float((ra-rb).abs().mean()),1))
def energy_w(cols,share):
    E=["C1_energy_intensity","C2_carbon_abatement","C5_cost_effectiveness"]; e=[c for c in cols if c in E]; o=[c for c in cols if c not in E]
    return pd.Series({c:(share/len(e) if c in E else (1-share)/len(o)) for c in cols})
