"""v3 checks (Leeds, Bradford): (a) cost-data coverage by LSOA and its relation to C5 and rank; C5 with imputed costs;
(b) reference per dwelling from total LSOA consumption / Census households; (c) consistency of corrected total vs corrected
gas x share + electricity; (d) excluding C6."""
import pandas as pd, numpy as np, json, sys, glob
sys.path.insert(0,"scripts"); from mcda import gra, combined_w; from mcda_v2 import *
import openpyxl
A=pd.read_csv("02_processed/v2/lsoa_table_v2.csv",index_col=0); out={}; rows=[]
cost=pd.read_parquet("02_processed/v2/cert_costs_2024prices.parquet")["cost_2024"]
# (a) coverage: dwellings with a priced package / all linked dwellings
Y=pd.concat(pd.read_parquet(p,columns=["certificate_number","PROP_TYPE","FLOOR_AREA_BAND","lsoa21cd"]) for p in glob.glob("02_processed/v2/yorks_dw/part*.parquet"))
Y["cost"]=Y.certificate_number.map(cost); LK=Y.groupby(["PROP_TYPE","FLOOR_AREA_BAND"]).cost.mean()
L=pd.read_parquet("02_processed/v2/leeds_dwelling_predictions_v2.parquet",columns=["certificate_number","PROP_TYPE","FLOOR_AREA_BAND","lsoa21cd"])
def W(P,w): return combined_w(P) if w=="objective" else (pd.Series(1/P.shape[1],index=P.columns) if w=="equal" else energy_w(P.columns,0.7))
for city,la,D in [("leeds","E08000035",L),("bradford","E08000032",Y[Y.lsoa21cd.isin(A.index[A.la=="E08000032"])])]:
    D=D.copy(); D["cost"]=D.certificate_number.map(cost); D["priced"]=D.cost.notna()
    cov=D.groupby("lsoa21cd").priced.mean()*100
    D["cost_imp"]=D.cost.fillna(D.set_index(["PROP_TYPE","FLOOR_AREA_BAND"]).index.map(LK).to_series(index=D.index))
    cimp=D.groupby("lsoa21cd").cost_imp.mean()
    M=pd.read_csv(f"03_outputs/v2/matrix_{city}_T0.csv",index_col=0); P=pd.read_csv(f"03_outputs/v2/matrix_{city}_T1c.csv",index_col=0); cov=cov.reindex(M.index)
    wE=pd.Series(1/6,index=M.columns); rM=rank(gra(M,wE)); rP=rank(gra(P,wE))
    out[f"{city}_cost_coverage"]=dict(median=round(float(cov.median()),1),p5=round(float(cov.quantile(.05)),1),min=round(float(cov.min()),1),max=round(float(cov.max()),1),
        rho_cov_C5_ref=round(float(cov.corr(M.C5_cost_effectiveness,method="spearman")),3),rho_cov_refrank_equal=round(float(cov.corr(rM,method="spearman")),3),
        rho_cov_absshift_equal=round(float(cov.corr((rP-rM).abs(),method="spearman")),3))
    C=A.loc[M.index]; Pi,Mi=P.copy(),M.copy()
    Pi["C5_cost_effectiveness"]=C.save*C.proxyc_total_mean/cimp.reindex(M.index); Mi["C5_cost_effectiveness"]=C.save*C.met_total_mean/cimp.reindex(M.index)
    for w in ["objective","equal","e70"]:
        wP=W(P,w); rows.append(dict(city=city,case="C5 with imputed costs (T1c vs T0-imp)",weights=w,**agree(gra(Pi,W(Pi,w)),gra(Mi,W(Pi,w)))))
        rows.append(dict(city=city,case="Reference: imputed vs base costs",weights=w,**agree(gra(Mi,wP),gra(M,wP))))
    # (b) alternative reference: total consumption / Census households
    tot={}
    for fuel,f in [("gas","LSOA_domestic_gas_2010-2024.xlsx"),("elec","LSOA_domestic_elec_2010-2024.xlsx")]:
        ws=openpyxl.load_workbook("01_raw/metered_benchmark/"+f,read_only=True)["2024"]
        tot[fuel]=pd.Series({r[4]:r[7] for r in ws.iter_rows(min_row=6,values_only=True) if r and r[4] in set(M.index)})
    g=tot["gas"].reindex(M.index).fillna(0)/C.households; e=tot["elec"].reindex(M.index)/C.households; t=g+e
    Ma=M.copy(); Ma["C1_energy_intensity"]=t/C.mean_tfa; Ma["C2_carbon_abatement"]=C.abate*(g*EG+e*EE)/1000; Ma["C5_cost_effectiveness"]=C.save*t/C.pkg_cost_2024
    out[f"{city}_alt_reference"]=dict(rho_total_alt_vs_meter=round(float(t.corr(C.met_total_mean,method="spearman")),3),ratio_median=round(float((t/C.met_total_mean).median()),3),
        ratio_p5=round(float((t/C.met_total_mean).quantile(.05)),3),ratio_p95=round(float((t/C.met_total_mean).quantile(.95)),3),MAPE_T1c_vs_alt=round(float(100*(abs(C.proxyc_total_mean-t)/t).mean()),1))
    for w in ["objective","equal","e70"]:
        wP=W(P,w); rows.append(dict(city=city,case="Alt. reference (households) vs base reference",weights=w,**agree(gra(Ma,wP),gra(M,wP))))
        rows.append(dict(city=city,case="T1c vs alt. reference (households)",weights=w,**agree(gra(P,wP),gra(Ma,wP))))
    # (c) consistency of corrected quantities
    comp=C.proxyc_gas_mean.fillna(0)*C.gas_share_epc+C.proxyc_elec_mean; d=100*(C.proxyc_total_mean-comp)/comp
    out[f"{city}_total_vs_components"]=dict(mean_pct=round(float(d.mean()),2),mean_abs_pct=round(float(d.abs().mean()),2),p95_abs_pct=round(float(d.abs().quantile(.95)),2),max_abs_pct=round(float(d.abs().max()),2))
    Pc=P.copy(); Pc["C1_energy_intensity"]=comp/C.mean_tfa; Pc["C5_cost_effectiveness"]=C.save*comp/C.pkg_cost_2024
    for w in ["objective","equal","e70"]:
        rows.append(dict(city=city,case="T1c with total = corrected gas + electricity",weights=w,**agree(gra(Pc,W(P,w)),gra(M,W(P,w)))))
    # (d) excluding C6
    for w in ["objective","equal","e70"]:
        P6,M6=P.drop(columns="C6_stock_homogeneity"),M.drop(columns="C6_stock_homogeneity"); w6=W(P6,w)
        rows.append(dict(city=city,case="T1c excl. C6",weights=w,**agree(gra(P6,w6),gra(M6,w6))))
        rows.append(dict(city=city,case="Reference excl. C6 vs reference",weights=w,**agree(gra(M6,W(M6,w)),gra(M,W(P,w)))))
R=pd.DataFrame(rows); R.to_csv("03_outputs/v2/checks_v3.csv",index=False); json.dump(out,open("03_outputs/v2/checks_v3.json","w"),indent=1)
print(json.dumps(out,indent=0)); pd.set_option("display.width",200); print(R.to_string(index=False))
