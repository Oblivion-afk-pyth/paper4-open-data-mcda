"""v2 data-reduction tiers (Leeds). All substituted group values (savings/abatement fractions, floor area, 2024-price costs, gas share)
come from EPC dwellings in the 14 OTHER Yorkshire authorities - no Leeds certificate information enters T2-T4 beyond the stated
tier inputs. T4 is compared with the six-criterion reference and with a five-criterion reference without C6."""
import pandas as pd, numpy as np, lightgbm as lgb, glob, json, sys
sys.path.insert(0,"scripts"); from mcda import gra, combined_w; from mcda_v2 import *
cost=pd.read_parquet("02_processed/v2/cert_costs_2024prices.parquet")["cost_2024"]
Y=pd.concat(pd.read_parquet(p,columns=["certificate_number","PROP_TYPE","FLOOR_AREA_BAND","MAIN_HEAT_FUEL","tfa_m2","epc_primary_kwh_m2","epc_potential_kwh_m2","co2_current_t","co2_potential_t"]) for p in glob.glob("02_processed/v2/yorks_dw/part*.parquet"))
Y["save"]=(1-Y.epc_potential_kwh_m2/Y.epc_primary_kwh_m2).clip(0,1); Y["abate"]=(1-Y.co2_potential_t/Y.co2_current_t).clip(0,1); Y["cost"]=Y.certificate_number.map(cost)
LTA=Y.groupby(["PROP_TYPE","FLOOR_AREA_BAND"])[["save","abate","tfa_m2","cost"]].mean(); LT=Y.groupby("PROP_TYPE")[["save","abate","tfa_m2","cost"]].mean()
ALL=Y[["save","abate","tfa_m2","cost"]].mean(); GS=(Y.MAIN_HEAT_FUEL==1).mean(); del Y
h=pd.read_parquet("02_processed/v2/leeds_dwelling_predictions_v2.parquet")
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); C=A[A.la=="E08000035"]
M=pd.read_csv("03_outputs/v2/matrix_leeds_T0.csv",index_col=0)
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"]}
def pr(t,fuel,X,feat):
    X=X[feat].copy()
    for c in feat: X[c]=pd.Categorical(X[c].astype(str),categories=CATS[c]) if c in CATS else X[c].astype(float)
    return lgb.Booster(model_file=f"models/need_{t}_{fuel}.txt").predict(X)
mats={"T1c":pd.read_csv("03_outputs/v2/matrix_leeds_T1c.csv",index_col=0),"T1":pd.read_csv("03_outputs/v2/matrix_leeds_T1.csv",index_col=0)}
tot={"T1c":C.proxyc_total_mean,"T1":C.proxy_total_mean}; isg=h.MAIN_HEAT_FUEL==1
for t in ["T2","T3","T4"]:
    X=pd.DataFrame(index=M.index)
    if t=="T4":
        g=h.groupby("lsoa21cd").IMD_BAND_ENG.first().to_frame()
        gas=pd.Series(pr("T4","gas",g,["IMD_BAND_ENG"]),index=g.index); el=pd.Series(pr("T4","elec",g,["IMD_BAND_ENG"]),index=g.index)
        share=GS; total=gas*share+el; tfa=ALL.tfa_m2; ab=ALL.abate; sv=ALL.save; cs=ALL.cost; C6=None
    else:
        feat=["PROP_TYPE","FLOOR_AREA_BAND","MAIN_HEAT_FUEL"] if t=="T2" else ["PROP_TYPE","MAIN_HEAT_FUEL"]
        d=h[["lsoa21cd","PROP_TYPE","FLOOR_AREA_BAND","MAIN_HEAT_FUEL","tfa_m2"]].copy(); d["pg"]=pr(t,"gas",d,feat)*isg.values; d["pe"]=pr(t,"elec",d,feat)
        lk=LTA if t=="T2" else LT; key=["PROP_TYPE","FLOOR_AREA_BAND"] if t=="T2" else ["PROP_TYPE"]
        d=d.join(lk,on=key,rsuffix="_lk")
        for c in ["save","abate","cost","tfa_m2_lk"]: 
            if c in d: d[c]=d[c].fillna(ALL[c.replace("_lk","")])
        d["tfa_use"]=d.tfa_m2 if t=="T2" else d.tfa_m2_lk
        d["arch"]=d.PROP_TYPE.astype(str)+("|"+d.FLOOR_AREA_BAND.astype(str) if t=="T2" else "")
        G=d.groupby("lsoa21cd"); share=G.MAIN_HEAT_FUEL.apply(lambda s:(s==1).mean())
        gas=d[d.MAIN_HEAT_FUEL==1].groupby("lsoa21cd").pg.mean(); el=G.pe.mean(); total=(d.pg+d.pe).groupby(d.lsoa21cd).mean()
        tfa=G.tfa_use.mean(); ab=G.abate.mean(); sv=G.save.mean(); cs=G.cost.mean(); C6=G.arch.agg(lambda s:s.value_counts(normalize=True).iloc[0]*100)
    X["C1_energy_intensity"]=total/tfa; X["C2_carbon_abatement"]=ab*(gas.reindex(M.index).fillna(0)*share*EG+el*EE)/1000
    X["C3_fuel_poverty"]=M.C3_fuel_poverty; X["C4_income_deprivation"]=M.C4_income_deprivation; X["C5_cost_effectiveness"]=sv*total/cs
    if C6 is not None: X["C6_stock_homogeneity"]=C6
    X=X.reindex(M.index); X.to_csv(f"03_outputs/v2/matrix_leeds_{t}.csv"); mats[t]=X; tot[t]=total
rows=[]; o=C.met_total_mean
for t,X in mats.items():
    tt=tot[t].reindex(M.index)
    for ref_name,Mr in [("6-criterion reference",M)]+([("5-criterion reference (no C6)",M.drop(columns="C6_stock_homogeneity"))] if t=="T4" else []):
        cols=[c for c in X.columns if c in Mr.columns]; Xr=X[cols]; Mr=Mr[cols] if ref_name.startswith("5") else Mr
        for w in ["objective","equal","e70"]:
            if w=="objective": wP=combined_w(Xr)
            elif w=="equal": wP=pd.Series(1/Xr.shape[1],index=Xr.columns)
            else: wP=energy_w(Xr.columns,0.7)
            wM=wP.reindex(Mr.columns).fillna(0) if ref_name.startswith("5") or t!="T4" else (combined_w(Mr) if w=="objective" else (pd.Series(1/6,index=Mr.columns) if w=="equal" else energy_w(Mr.columns,0.7)))
            a=agree(gra(Xr,wP),gra(Mr,wM))
            rows.append(dict(tier=t,reference=ref_name,weights=w,L1_MAPE=round(float(100*(abs(tt-o)/o).mean()),1),L1_rho=round(float(tt.corr(o,method="spearman")),3),**a))
R=pd.DataFrame(rows); R.to_csv("03_outputs/v2/tiers_v2.csv",index=False); print(R.to_string(index=False))
