"""Leeds 053: building-level priority scores (illustrative, not validated) with the postcode objective weight vector
(T1c, eight criteria); written to the IFC as Pset_Paper4_Priority together with the postcode rank and MC P(top 20%)."""
import os,sys,json,shutil,numpy as np,pandas as pd,geopandas as gpd,ifcopenshell,ifcopenshell.api as api
D=(__import__("paths").ROOT+""); P=D+"02_processed/"; O=P+"v4_district/"; OUT=D+"03_outputs/v4_district/"
sys.path.insert(0,D+"scripts"); from mcda import gra,combined_w; from mcda_v2 import matrix,rank,EG,EE
T=pd.read_csv(O+"l053_postcode_table.csv",index_col=0); Tk=T[T.keep]
BIM=["C7_form_factor","C8_pv_area_dw"]; Pm=matrix(Tk,"T1c").join(Tk[BIM]); w=combined_w(Pm)
pscore=gra(Pm,w); prank=rank(pscore); ptop=pd.read_csv(OUT+"l053_montecarlo_ptop20.csv",index_col=0)["objective"]
A=pd.read_csv(P+"v2/lsoa_table_v2.csv",index_col=0); cost=pd.read_parquet(P+"v2/cert_costs_2024prices.parquet")["cost_2024"]
h=pd.read_csv(O+"l053_epc_linked.csv",low_memory=False); h=h[h.bid.notna()&(h.lodgement_year<=2024)].copy()
f=lambda k:h.lsoa21cd.map(A[f"proxyc_{k}_mean"]/A[f"proxy_{k}_mean"])
g=h.MAIN_HEAT_FUEL==1
h["totc"]=(h.pred_gas+h.pred_elec)*f("total"); h["gasc"]=h.pred_gas.where(g,0)*f("gas"); h["elecc"]=h.pred_elec*f("elec")
h["save"]=(1-h.epc_potential_kwh_m2/h.epc_primary_kwh_m2).clip(0,1); h["abate"]=(1-h.co2_potential_t/h.co2_current_t).clip(0,1)
h["co2"]=(h.gasc*EG+h.elecc*EE)/1000; h["abate_t"]=h.abate*h.co2; h["save_kwh"]=h.save*h.totc; h["cost"]=h.certificate_number.map(cost)
B=h.groupby("bid").agg(totc=("totc","sum"),tfa=("tfa_m2","sum"),abate_t=("abate_t","mean"),save_kwh=("save_kwh","sum"),cost=("cost","sum"),
  lsoa=("lsoa21cd",lambda s:s.mode().iat[0]),postcode=("postcode",lambda s:s.mode().iat[0] if s.notna().any() else None),n=("totc","size"))
b=gpd.read_file(O+"l053_buildings_v2.gpkg").set_index("bid")
B=B.join(b[["form_factor","pv_area_m2","lidar_ok"]]); B=B[B.lidar_ok.astype(bool)&(B.tfa>0)&(B.cost>0)]
X=pd.DataFrame(index=B.index)
X["C1_energy_intensity"]=B.totc/B.tfa; X["C2_carbon_abatement"]=B.abate_t; X["C3_fuel_poverty"]=B.lsoa.map(A.fuel_poverty_pct); X["C4_income_deprivation"]=B.lsoa.map(A.income_score)
X["C5_cost_effectiveness"]=B.save_kwh/B.cost; X["C6_stock_homogeneity"]=B.postcode.map(T.C6_stock_homogeneity)
X["C7_form_factor"]=B.form_factor; X["C8_pv_area_dw"]=B.pv_area_m2/B.n
X=X.replace([np.inf,-np.inf],np.nan); print("NaN by criterion before drop:",X.isna().sum().to_dict()); X=X.dropna()
for c in X: X[c]=X[c].clip(X[c].quantile(0.01),X[c].quantile(0.99))   # winsorise 1/99% (building-level outliers)
bs=gra(X,w[X.columns]); br=rank(bs)
S=pd.DataFrame({"score":bs,"rank":br,"postcode":B.loc[X.index,"postcode"]})
S["postcode_rank"]=S.postcode.map(prank); S["postcode_Ptop20"]=S.postcode.map(ptop); S["top20_building"]=S["rank"]<=int(round(0.2*len(S)))
S.to_csv(OUT+"l053_building_scores.csv")
# consistency: mean building score by postcode vs postcode score
c=S.groupby("postcode").score.mean().to_frame("bmean").join(pscore.rename("pscore")).dropna()
from scipy.stats import spearmanr
cons=dict(n_buildings_scored=len(S),rho_postcode_vs_mean_building=round(float(spearmanr(c.bmean,c.pscore).correlation),3),
  share_top20_buildings_in_top20_postcodes=round(float((S[S.top20_building].postcode_rank<=int(round(0.2*len(Tk)))).mean()),3))
# write to IFC
f_=ifcopenshell.open(OUT+"Leeds053_LOD1.ifc"); n=0
for bd in f_.by_type("IfcBuilding"):
    bid=int(bd.Name.split("-")[1])
    if bid not in S.index: continue
    r=S.loc[bid]; ps=api.run("pset.add_pset",f_,product=bd,name="Pset_Paper4_Priority")
    api.run("pset.edit_pset",f_,pset=ps,properties={"GRAScore":float(r.score),"BuildingRank":int(r["rank"]),"BuildingsRanked":len(S),
      "PostcodeRank":None if pd.isna(r.postcode_rank) else int(r.postcode_rank),"PostcodesRanked":len(Tk),
      "PostcodeProbTop20":None if pd.isna(r.postcode_Ptop20) else float(r.postcode_Ptop20),"Top20Building":bool(r.top20_building),
      "Note":"Illustrative; building ranks not validated (no building-level meter data). Weights: postcode objective vector, T1c, C1-C8."}); n+=1
tmp=(__import__("paths").WORK+"Leeds053_LOD1_priority.ifc"); f_.write(tmp); shutil.copy(tmp,OUT+"Leeds053_LOD1_priority.ifc")
cons["ifc_buildings_with_priority"]=n; cons["weights"]={k:round(float(v),3) for k,v in w.items()}
json.dump(cons,open(OUT+"l053_building_scores.json","w"),indent=1); print(json.dumps(cons,indent=1))
