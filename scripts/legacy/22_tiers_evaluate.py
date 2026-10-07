"""RQ3: data-reduction tiers T1c,T1,T2,T3,T4 vs metered T0 (Level 1 total energy + Level 2 ranking)."""
import pandas as pd, numpy as np, lightgbm as lgb, glob, re, os, sys
sys.path.insert(0,"scripts"); from mcda import *; from harmonise import harmonise
EG,EE=0.18290,0.20705
h=pd.read_parquet("02_processed/leeds_dwelling_predictions.parquet")
h["save_frac"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1); h["abate"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
# group lookups from Yorkshire outside Leeds (cached)
LK="02_processed/yorks_group_lookups.csv"
if not os.path.exists(LK):
    iod=pd.read_csv("01_raw/deprivation/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",usecols=[0,6]); dec=iod.set_index(iod.columns[0])[iod.columns[1]]
    e=pd.read_csv("02_processed/yorks_epc_latest.csv",dtype=str,usecols=["certificate_number","lsoa21cd","property_type","built_form","construction_age_band","total_floor_area","current_energy_rating","main_fuel","mains_gas_flag","photo_supply","energy_consumption_current","energy_consumption_potential","co2_emissions_current","co2_emissions_potential"])
    y=harmonise(e,dec); y["save_frac"]=(1-y.epc_potential_kwh_m2/y.epc_primary_kwh_m2).clip(0,1); y["abate"]=(1-y.co2_potential_t/y.co2_current_t).clip(0,1)
    y.groupby(["PROP_TYPE","FLOOR_AREA_BAND"])[["save_frac","abate","tfa_m2"]].mean().to_csv(LK)
    y.groupby("PROP_TYPE")[["save_frac","abate","tfa_m2"]].mean().to_csv(LK.replace(".csv","_type.csv"))
    pd.DataFrame({"save_frac":[y.save_frac.mean()],"abate":[y.abate.mean()],"tfa_m2":[y.tfa_m2.mean()],"gas_share":[(y.MAIN_HEAT_FUEL==1).mean()]}).to_csv(LK.replace(".csv","_all.csv"),index=False)
LTA=pd.read_csv(LK); LTA["FLOOR_AREA_BAND"]=LTA.FLOOR_AREA_BAND.astype(float); LT=pd.read_csv(LK.replace(".csv","_type.csv")).set_index("PROP_TYPE"); LA_=pd.read_csv(LK.replace(".csv","_all.csv")).iloc[0]
# costs: Leeds recommendation totals averaged by group (group level only)
def mid(s):
    v=[float(x.replace(",","")) for x in re.findall(r"£\s*([\d,]+)",str(s))]; return np.mean(v) if v else np.nan
cost=pd.concat(pd.read_csv(p,usecols=["certificate_number","indicative_cost"],dtype=str).assign(c=lambda d:d.indicative_cost.map(mid)).groupby("certificate_number").c.sum() for p in glob.glob("02_processed/epc_parts/recommendations-*_leeds.csv")).groupby(level=0).sum()
h["cost"]=h.certificate_number.map(cost)
CT=h.groupby(["PROP_TYPE","FLOOR_AREA_BAND"]).cost.mean(); CTt=h.groupby("PROP_TYPE").cost.mean(); CTall=h.cost.mean()
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"]}
def pr(tier,fuel,X,feat):
    X=X[feat].copy()
    for c in feat: X[c]=pd.Categorical(X[c].astype(str),categories=CATS[c]) if c in CATS else X[c].astype(float)
    return lgb.Booster(model_file=f"models/need_{tier}_{fuel}.txt").predict(X)
M=pd.read_csv("03_outputs/matrix_metered_T0.csv",index_col=0); T1=pd.read_csv("03_outputs/matrix_proxy_T1.csv",index_col=0); T1c=pd.read_csv("03_outputs/matrix_proxy_T1c.csv",index_col=0)
L1=pd.read_csv("03_outputs/level1_lsoa_estimates_vs_metered.csv",index_col=0)
soc=M[["C3_fuel_poverty","C4_income_deprivation"]]
mats={"T1c":T1c,"T1":T1}; tot={"T1":L1.proxy_total_mean,"T1c":pd.read_csv("02_processed/leeds_lsoa_T1c.csv",index_col=0).proxyc_total_mean}
isg=(h.MAIN_HEAT_FUEL==1)
for tier in ["T2","T3","T4"]:
    d=h.copy()
    if tier=="T4":
        g=pd.DataFrame({"IMD_BAND_ENG":d.groupby("lsoa21cd").IMD_BAND_ENG.first()})
        gas=pd.Series(pr("T4","gas",g,["IMD_BAND_ENG"]),index=g.index); el=pd.Series(pr("T4","elec",g,["IMD_BAND_ENG"]),index=g.index)
        share=LA_.gas_share; total=gas*share+el; tfa=LA_.tfa_m2
        abate=pd.Series(LA_.abate,index=g.index); sf=pd.Series(LA_.save_frac,index=g.index); cst=pd.Series(CTall,index=g.index); C6=None
    else:
        feat=["PROP_TYPE","FLOOR_AREA_BAND","MAIN_HEAT_FUEL"] if tier=="T2" else ["PROP_TYPE","MAIN_HEAT_FUEL"]
        d["pg"]=pr(tier,"gas",d,feat)*isg; d["pe"]=pr(tier,"elec",d,feat)
        if tier=="T2":
            d=d.merge(LTA,on=["PROP_TYPE","FLOOR_AREA_BAND"],how="left",suffixes=("","_lk")); d["cst"]=[CT.get((a,b),CTall) for a,b in zip(d.PROP_TYPE,d.FLOOR_AREA_BAND)]
            d["tfa_use"]=d.tfa_m2; d["arch"]=d.PROP_TYPE.astype(str)+"|"+d.FLOOR_AREA_BAND.astype(str)
        else:
            d=d.join(LT,on="PROP_TYPE",rsuffix="_lk"); d["cst"]=d.PROP_TYPE.map(CTt).fillna(CTall)
            d["tfa_use"]=d.tfa_m2_lk; d["arch"]=d.PROP_TYPE.astype(str)
        G=d.groupby("lsoa21cd"); share=G.MAIN_HEAT_FUEL.apply(lambda s:(s==1).mean())
        gas=d[d.MAIN_HEAT_FUEL==1].groupby("lsoa21cd").pg.mean(); el=G.pe.mean(); total=(d.pg+d.pe).groupby(d.lsoa21cd).mean()
        tfa=G.tfa_use.mean(); abate=G.abate_lk.mean(); sf=G.save_frac_lk.mean(); cst=G.cst.mean()
        C6=G.arch.agg(lambda s:s.value_counts(normalize=True).iloc[0]*100)
    X=pd.DataFrame(index=M.index)
    X["C1_energy_intensity"]=total/tfa
    X["C2_carbon_abatement"]=abate*(gas.reindex(M.index).fillna(0)*share*EG+el*EE)/1000
    X["C3_fuel_poverty"]=soc.C3_fuel_poverty; X["C4_income_deprivation"]=soc.C4_income_deprivation
    X["C5_cost_effectiveness"]=sf*total/cst
    if C6 is not None: X["C6_delivery_eff"]=C6
    X.to_csv(f"03_outputs/matrix_proxy_{tier}.csv"); mats[tier]=X; tot[tier]=total
rows=[]
for tier,X in mats.items():
    t=tot[tier].reindex(M.index); o=L1.met_total_mean
    r=dict(tier=tier,n_inputs_criteria=X.shape[1],L1_MAPE=round(100*(abs(t-o)/o).mean(),1),L1_rho=round(t.corr(o,method="spearman"),3))
    a=compare(gra(X,combined_w(X)),gra(M,combined_w(M))); e=compare(gra(X,pd.Series(1/X.shape[1],index=X.columns)),gra(M,pd.Series(1/6,index=M.columns)))
    r.update({"rho_objW":a["spearman"],"top20_objW":a["top20_overlap_pct"],"rho_eqW":e["spearman"],"top20_eqW":e["top20_overlap_pct"]})
    rows.append(r)
R=pd.DataFrame(rows); R.to_csv("03_outputs/rq3_data_reduction_curve.csv",index=False); print(R.to_string(index=False))
