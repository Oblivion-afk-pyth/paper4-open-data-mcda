"""Transfer models: train LightGBM on NEED 2026 (England minus Yorkshire & Humber), test on Yorkshire & Humber.
Usage: python 09_train_transfer_models.py gas|elec"""
import sys, json, time, numpy as np, pandas as pd, lightgbm as lgb
fuel=sys.argv[1]; t0=time.time()
CATS={"PROP_TYPE":["Detached","Semi detached","Mid terrace","End terrace","Bungalow","Flat"],
      "EPC":["A/B","C","D","E","F/G"]}
FEAT=["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC","IMD_BAND_ENG","PV_FLAG"]+(["MAIN_HEAT_FUEL"] if fuel=="elec" else [])
Y={"gas":("Gcons2024","GasValFlag2024"),"elec":("Econs2024","ElecValFlag2024")}[fuel]
d=pd.read_parquet("02_processed/need2026_england_slim.parquet",columns=FEAT+list(Y)+["REGION","MAIN_HEAT_FUEL"] if fuel=="gas" else FEAT+list(Y)+["REGION"])
d=d[(d[Y[1]]=="V")&(d.EPC.astype(str)!="No EPC")]
if fuel=="gas": d=d[d.MAIN_HEAT_FUEL==1]
d=d.dropna(subset=FEAT+[Y[0]])
def prep(x):
    x=x[FEAT].copy()
    for c,v in CATS.items(): x[c]=pd.Categorical(x[c].astype(str),categories=v)
    for c in FEAT:
        if c not in CATS: x[c]=x[c].astype(float)
    return x
test=d[d.REGION.astype(str)=="E12000003"]; train=d[d.REGION.astype(str)!="E12000003"]
train=train.sample(n=min(len(train),1_200_000),random_state=42)
p=dict(objective="regression",learning_rate=0.05,num_leaves=63,min_data_in_leaf=200,feature_fraction=0.9,bagging_fraction=0.8,bagging_freq=1,verbose=-1,num_threads=2,seed=42)
m=lgb.train(p,lgb.Dataset(prep(train),train[Y[0]],categorical_feature=list(CATS)),num_boost_round=400)
yp=m.predict(prep(test)); yt=test[Y[0]].values
r2=1-((yt-yp)**2).sum()/((yt-yt.mean())**2).sum()
res=dict(fuel=fuel,n_train=len(train),n_test_yorkshire=len(test),r2_household=round(r2,3),mae_kwh=round(float(np.abs(yt-yp).mean())),
         mean_obs=round(float(yt.mean())),mean_pred=round(float(yp.mean())),bias_pct=round(100*(yp.mean()-yt.mean())/yt.mean(),2),
         importance=dict(zip(FEAT,[int(v) for v in m.feature_importance("gain")/1e6])),seconds=round(time.time()-t0))
# cell-level (group-mean) accuracy: how well the model reproduces average consumption of each property-type x age x size x EPC cell
g=test.assign(pred=yp).groupby(["PROP_TYPE","PROP_AGE_BAND","FLOOR_AREA_BAND","EPC"],observed=True).agg(obs=(Y[0],"mean"),pred=("pred","mean"),n=("pred","size")).query("n>=50")
res["r2_cell_means"]=round(1-((g.obs-g.pred)**2*g.n).sum()/((g.obs-np.average(g.obs,weights=g.n))**2*g.n).sum(),3)
m.save_model(f"models/need_transfer_{fuel}.txt"); json.dump(res,open(f"models/need_transfer_{fuel}_metrics.json","w"),indent=1)
print(json.dumps(res,indent=1))
