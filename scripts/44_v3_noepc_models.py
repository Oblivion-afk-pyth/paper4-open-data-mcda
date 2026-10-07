"""v3: transfer models WITHOUT the EPC rating feature (NEED EPC band may post-date 2024 consumption). Same settings/seed as 09.
Trains, tests on Yorkshire & Humber, predicts Leeds and the other Yorkshire dwellings -> LSOA proxy means (noepc)."""
import sys, json, numpy as np, pandas as pd, lightgbm as lgb, glob
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"]}
out={}
def prep(x,FEAT):
    x=x[FEAT].copy()
    for c,v in CATS.items(): x[c]=pd.Categorical(x[c].astype(str),categories=v)
    for c in FEAT:
        if c not in CATS: x[c]=x[c].astype(float)
    return x
FEATS={}
for fuel in ["gas","elec"]:
    FEAT=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","IMD_BAND_ENG","PV_FLAG"]+(["MAIN_HEAT_FUEL"] if fuel=="elec" else []); FEATS[fuel]=FEAT
    Y={"gas":("Gcons2024","GasValFlag2024"),"elec":("Econs2024","ElecValFlag2024")}[fuel]
    cols=list(dict.fromkeys(FEAT+list(Y)+["REGION","EPC","MAIN_HEAT_FUEL"]))
    d=pd.read_parquet("02_processed/need2026_england_slim.parquet",columns=cols)
    d=d[(d[Y[1]]=="V")&(d.EPC.astype(str)!="No EPC")]      # same record set as the EPC-feature models
    if fuel=="gas": d=d[d.MAIN_HEAT_FUEL==1]
    d=d.dropna(subset=FEAT+[Y[0]])
    test=d[d.REGION.astype(str)=="E12000003"]; train=d[d.REGION.astype(str)!="E12000003"].sample(n=1_200_000,random_state=42)
    p=dict(objective="regression",learning_rate=0.05,num_leaves=63,min_data_in_leaf=200,feature_fraction=0.9,bagging_fraction=0.8,bagging_freq=1,verbose=-1,num_threads=2,seed=42)
    m=lgb.train(p,lgb.Dataset(prep(train,FEAT),train[Y[0]],categorical_feature=list(CATS)),num_boost_round=400)
    yp=m.predict(prep(test,FEAT)); yt=test[Y[0]].values
    g=test.assign(pred=yp).groupby(["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC"],observed=True).agg(obs=(Y[0],"mean"),pred=("pred","mean"),n=("pred","size")).query("n>=50")
    out[fuel]=dict(n_train=len(train),n_test=len(test),r2_household=round(float(1-((yt-yp)**2).sum()/((yt-yt.mean())**2).sum()),3),
        r2_cell_means=round(float(1-((g.obs-g.pred)**2*g.n).sum()/((g.obs-np.average(g.obs,weights=g.n))**2*g.n).sum()),3),bias_pct=round(float(100*(yp.mean()-yt.mean())/yt.mean()),2))
    m.save_model(f"models/need_noepc_{fuel}.txt"); del d,train,test
def pred(h):
    h=h.copy(); g=h.MAIN_HEAT_FUEL==1
    h["pg"]=lgb.Booster(model_file="models/need_noepc_gas.txt").predict(prep(h,FEATS["gas"]))*g
    h["pe"]=lgb.Booster(model_file="models/need_noepc_elec.txt").predict(prep(h,FEATS["elec"]))
    return pd.DataFrame({"noepc_gas_mean":h[g].groupby("lsoa21cd").pg.mean(),"noepc_elec_mean":h.groupby("lsoa21cd").pe.mean(),"noepc_total_mean":(h.pg+h.pe).groupby(h.lsoa21cd).mean()})
parts=[pred(pd.read_parquet("02_processed/v2/leeds_dwelling_predictions_v2.parquet"))]
for f in sorted(glob.glob("02_processed/v2/yorks_dw/part*.parquet")): parts.append(pred(pd.read_parquet(f)))
pd.concat(parts).groupby(level=0).mean().to_csv("02_processed/v3_noepc_lsoa.csv")
json.dump(out,open("03_outputs/v2/noepc_models.json","w"),indent=1); print(json.dumps(out))
