"""v3: LSOA means of no-EPC predictions (sum/count aggregation across chunks)."""
import pandas as pd, lightgbm as lgb, glob
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"]}
FG=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","IMD_BAND_ENG","PV_FLAG"]; FE=FG+["MAIN_HEAT_FUEL"]
mg=lgb.Booster(model_file="models/need_noepc_gas.txt"); me=lgb.Booster(model_file="models/need_noepc_elec.txt")
def prep(x,F):
    x=x[F].copy()
    for c in F: x[c]=pd.Categorical(x[c].astype(str),categories=CATS[c]) if c in CATS else x[c].astype(float)
    return x
S=[]
def agg(h):
    g=(h.MAIN_HEAT_FUEL==1); pg=mg.predict(prep(h,FG))*g; pe=me.predict(prep(h,FE))
    d=pd.DataFrame({"l":h.lsoa21cd.values,"gs":pg.where(g),"e":pe,"t":pg+pe})
    S.append(d.groupby("l").agg(gs=("gs","sum"),gn=("gs","count"),es=("e","sum"),en=("e","count"),ts=("t","sum"),tn=("t","count")))
agg(pd.read_parquet("02_processed/v2/leeds_dwelling_predictions_v2.parquet"))
for f in sorted(glob.glob("02_processed/v2/yorks_dw/part*.parquet")): agg(pd.read_parquet(f))
A=pd.concat(S).groupby(level=0).sum()
pd.DataFrame({"noepc_gas_mean":A.gs/A.gn,"noepc_elec_mean":A.es/A.en,"noepc_total_mean":A.ts/A.tn}).to_csv("02_processed/v3_noepc_lsoa.csv"); print(len(A))
